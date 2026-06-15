"""HawkPhish - Proxy Routes"""
import re
import time
import socket
import socks
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import ProxyConfig
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/api/proxies", tags=["Proxies"])


class ProxyCreate(BaseModel):
    name: str
    proxy_type: str = "http"
    host: str
    port: int
    username: Optional[str] = ""
    password: Optional[str] = ""
    is_active: bool = True


@router.get("")
async def list_proxies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProxyConfig).order_by(ProxyConfig.created_at.desc()))
    proxies = result.scalars().all()
    return [{
        "id": p.id, "name": p.name, "proxy_type": p.proxy_type,
        "host": p.host, "port": p.port, "username": p.username,
        "is_active": p.is_active, "is_healthy": p.is_healthy,
        "last_health_check": p.last_health_check.isoformat() if p.last_health_check else None,
        "total_uses": p.total_uses, "total_failures": p.total_failures,
        "avg_latency": round(p.avg_latency, 2),
        "created_at": p.created_at.isoformat(),
    } for p in proxies]


@router.post("")
async def create_proxy(data: ProxyCreate, db: AsyncSession = Depends(get_db)):
    proxy = ProxyConfig(**data.model_dump())
    db.add(proxy)
    await db.commit()
    await db.refresh(proxy)
    return {"id": proxy.id, "message": "Proxy created"}


@router.get("/{proxy_id}")
async def get_proxy(proxy_id: int, db: AsyncSession = Depends(get_db)):
    proxy = await db.get(ProxyConfig, proxy_id)
    if not proxy:
        raise HTTPException(404, "Proxy not found")
    return {
        "id": proxy.id, "name": proxy.name, "proxy_type": proxy.proxy_type,
        "host": proxy.host, "port": proxy.port, "username": proxy.username,
        "is_active": proxy.is_active, "is_healthy": proxy.is_healthy,
        "last_health_check": proxy.last_health_check.isoformat() if proxy.last_health_check else None,
        "total_uses": proxy.total_uses, "total_failures": proxy.total_failures,
        "avg_latency": round(proxy.avg_latency, 2),
        "created_at": proxy.created_at.isoformat(),
    }


@router.put("/{proxy_id}")
async def update_proxy(proxy_id: int, data: ProxyCreate, db: AsyncSession = Depends(get_db)):
    proxy = await db.get(ProxyConfig, proxy_id)
    if not proxy:
        raise HTTPException(404, "Proxy not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(proxy, k, v)
    await db.commit()
    return {"message": "Proxy updated"}


@router.delete("/{proxy_id}")
async def delete_proxy(proxy_id: int, db: AsyncSession = Depends(get_db)):
    proxy = await db.get(ProxyConfig, proxy_id)
    if not proxy:
        raise HTTPException(404, "Proxy not found")
    await db.delete(proxy)
    await db.commit()
    return {"message": "Proxy deleted"}


@router.delete("")
async def delete_all_proxies(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import delete
    await db.execute(delete(ProxyConfig))
    await db.commit()
    return {"message": "All proxies deleted"}


@router.post("/{proxy_id}/test")
async def test_proxy(proxy_id: int, db: AsyncSession = Depends(get_db)):
    proxy = await db.get(ProxyConfig, proxy_id)
    if not proxy:
        raise HTTPException(404, "Proxy not found")

    start = time.time()
    try:
        if proxy.proxy_type == "socks5":
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, proxy.host, proxy.port,
                       username=proxy.username or None, password=proxy.password or None)
            s.settimeout(10)
            s.connect(("imap.gmail.com", 993))
            s.close()
        elif proxy.proxy_type == "socks4":
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS4, proxy.host, proxy.port)
            s.settimeout(10)
            s.connect(("imap.gmail.com", 993))
            s.close()
        elif proxy.proxy_type == "http":
            import httpx
            proxy_url = f"http://{proxy.host}:{proxy.port}"
            if proxy.username:
                proxy_url = f"http://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"
            async with httpx.AsyncClient(proxy=proxy_url, timeout=10) as client:
                r = await client.get("https://httpbin.org/ip")
                if r.status_code != 200:
                    raise Exception(f"HTTP {r.status_code}")
        elif proxy.proxy_type == "https":
            import httpx
            proxy_url = f"https://{proxy.host}:{proxy.port}"
            if proxy.username:
                proxy_url = f"https://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"
            async with httpx.AsyncClient(proxy=proxy_url, timeout=10) as client:
                r = await client.get("https://httpbin.org/ip")
                if r.status_code != 200:
                    raise Exception(f"HTTP {r.status_code}")

        latency = (time.time() - start) * 1000
        proxy.is_healthy = True
        proxy.last_health_check = datetime.utcnow()
        proxy.avg_latency = (proxy.avg_latency * 0.7) + (latency * 0.3)
        await db.commit()
        return {"healthy": True, "latency": round(latency, 1), "proxy_type": proxy.proxy_type}

    except Exception as e:
        proxy.is_healthy = False
        proxy.last_health_check = datetime.utcnow()
        proxy.total_failures += 1
        await db.commit()
        return {"healthy": False, "error": str(e), "latency": 0}


@router.post("/test-all")
async def test_all_proxies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProxyConfig).where(ProxyConfig.is_active == True))
    proxies = result.scalars().all()
    results = []
    for proxy in proxies:
        start = time.time()
        try:
            if proxy.proxy_type in ("socks5", "socks4"):
                ptype = socks.SOCKS5 if proxy.proxy_type == "socks5" else socks.SOCKS4
                s = socks.socksocket()
                s.set_proxy(ptype, proxy.host, proxy.port,
                           username=proxy.username or None, password=proxy.password or None)
                s.settimeout(10)
                s.connect(("imap.gmail.com", 993))
                s.close()
            else:
                import httpx
                scheme = "https" if proxy.proxy_type == "https" else "http"
                auth = f"{proxy.username}:{proxy.password}@" if proxy.username else ""
                proxy_url = f"{scheme}://{auth}{proxy.host}:{proxy.port}"
                async with httpx.AsyncClient(proxy=proxy_url, timeout=10) as client:
                    r = await client.get("https://httpbin.org/ip")
                    if r.status_code != 200:
                        raise Exception(f"HTTP {r.status_code}")

            latency = (time.time() - start) * 1000
            proxy.is_healthy = True
            proxy.last_health_check = datetime.utcnow()
            proxy.avg_latency = (proxy.avg_latency * 0.7) + (latency * 0.3)
            results.append({"id": proxy.id, "name": proxy.name, "healthy": True, "latency": round(latency, 1)})
        except Exception as e:
            proxy.is_healthy = False
            proxy.total_failures += 1
            results.append({"id": proxy.id, "name": proxy.name, "healthy": False, "error": str(e)})
    await db.commit()
    return results


@router.post("/bulk-import")
async def bulk_import_proxies(data: dict, db: AsyncSession = Depends(get_db)):
    raw = data.get("proxies", "")
    if not raw:
        raise HTTPException(400, "No proxies provided")

    lines = raw.strip().split('\n')
    imported = 0
    skipped = 0

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        parsed = _parse_proxy_line(line)
        if not parsed:
            skipped += 1
            continue

        proxy = ProxyConfig(**parsed)
        db.add(proxy)
        imported += 1

    await db.commit()
    return {"imported": imported, "skipped": skipped}


def _parse_proxy_line(line: str) -> dict:
    """Parse proxy lines in formats:
    - type://host:port:user:pass
    - type://host:port
    - host:port:user:pass
    - host:port
    - type|host|port|user|pass
    - user:pass@host:port
    """
    proxy_type = "http"

    # type://host:port:user:pass
    m = re.match(r'^(https?|socks[45])://(.+)$', line)
    if m:
        proxy_type = m.group(1)
        rest = m.group(2)
        # user:pass@host:port
        am = re.match(r'^(.+?):(.+?)@(.+?):(\d+)$', rest)
        if am:
            return {"name": f"{am.group(3)}:{am.group(4)}", "proxy_type": proxy_type,
                    "host": am.group(3), "port": int(am.group(4)),
                    "username": am.group(1), "password": am.group(2)}
        # host:port
        parts = rest.split(':')
        if len(parts) >= 2:
            return {"name": f"{parts[0]}:{parts[1]}", "proxy_type": proxy_type,
                    "host": parts[0], "port": int(parts[1])}

    # pipe format: type|host|port|user|pass
    if '|' in line:
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 3:
            pt = parts[0] if parts[0] in ('http','https','socks4','socks5') else 'http'
            if pt == parts[0]:
                host, port = parts[1], int(parts[2])
            else:
                host, port = parts[0], int(parts[1])
            user = parts[3] if len(parts) > 3 else ""
            pwd = parts[4] if len(parts) > 4 else ""
            return {"name": f"{host}:{port}", "proxy_type": pt, "host": host, "port": port,
                    "username": user, "password": pwd}

    # user:pass@host:port
    m = re.match(r'^(.+?):(.+?)@(.+?):(\d+)$', line)
    if m:
        return {"name": f"{m.group(3)}:{m.group(4)}", "proxy_type": "http",
                "host": m.group(3), "port": int(m.group(4)),
                "username": m.group(1), "password": m.group(2)}

    # host:port
    parts = line.split(':')
    if len(parts) >= 2:
        try:
            port = int(parts[1])
            return {"name": f"{parts[0]}:{port}", "proxy_type": "http",
                    "host": parts[0], "port": port}
        except ValueError:
            pass

    return None
