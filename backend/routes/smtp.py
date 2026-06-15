"""HawkPhish - SMTP Routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import SMTPConfig
from services.smtp_service import SMTPHealthChecker, SMTPSender
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import re

router = APIRouter(prefix="/api/smtp", tags=["SMTP"])


class SMTPCreate(BaseModel):
    name: str
    provider: str = "custom"
    host: Optional[str] = None
    port: int = 587
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    from_email: str
    from_name: str = ""
    use_tls: bool = True
    max_emails: int = 500
    rate_limit: int = 50
    retry_count: int = 3
    profile_group: str = "default"


@router.get("")
async def list_smtp(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SMTPConfig))
    configs = result.scalars().all()
    return [{
        "id": c.id, "name": c.name, "provider": c.provider,
        "host": c.host, "port": c.port, "from_email": c.from_email,
        "from_name": c.from_name, "max_emails": c.max_emails,
        "emails_sent": c.emails_sent, "is_active": c.is_active,
        "is_healthy": c.is_healthy, "last_health_check": c.last_health_check.isoformat() if c.last_health_check else None,
        "profile_group": c.profile_group, "created_at": c.created_at.isoformat(),
    } for c in configs]


@router.post("")
async def create_smtp(data: SMTPCreate, db: AsyncSession = Depends(get_db)):
    config = SMTPConfig(**data.model_dump())
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return {"id": config.id, "message": "SMTP created"}


@router.put("/{smtp_id}")
async def update_smtp(smtp_id: int, data: SMTPCreate, db: AsyncSession = Depends(get_db)):
    config = await db.get(SMTPConfig, smtp_id)
    if not config:
        raise HTTPException(404, "SMTP not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(config, k, v)
    await db.commit()
    return {"message": "SMTP updated"}


@router.delete("/{smtp_id}")
async def delete_smtp(smtp_id: int, db: AsyncSession = Depends(get_db)):
    config = await db.get(SMTPConfig, smtp_id)
    if not config:
        raise HTTPException(404, "SMTP not found")
    await db.delete(config)
    await db.commit()
    return {"message": "SMTP deleted"}


@router.post("/{smtp_id}/health")
async def check_health(smtp_id: int, db: AsyncSession = Depends(get_db)):
    config = await db.get(SMTPConfig, smtp_id)
    if not config:
        raise HTTPException(404, "SMTP not found")

    checker = SMTPHealthChecker()
    result = await checker.check({
        "provider": config.provider, "host": config.host, "port": config.port,
        "username": config.username, "password": config.password,
        "api_key": config.api_key, "use_tls": config.use_tls,
        "domain": config.from_email.split("@")[1] if "@" in config.from_email else "",
    })

    config.is_healthy = result["healthy"]
    config.last_health_check = datetime.utcnow()
    await db.commit()

    return {"healthy": result["healthy"], "latency": result["latency"], "error": result.get("error")}


@router.post("/{smtp_id}/test-send")
async def test_send_email(smtp_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    config = await db.get(SMTPConfig, smtp_id)
    if not config:
        raise HTTPException(404, "SMTP not found")

    to_email = data.get("to_email")
    if not to_email:
        raise HTTPException(400, "to_email is required")

    sender = SMTPSender()
    result = await sender.send(
        {
            "provider": config.provider,
            "host": config.host,
            "port": config.port,
            "username": config.username,
            "password": config.password,
            "api_key": config.api_key,
            "use_tls": config.use_tls,
            "domain": config.from_email.split("@")[1] if "@" in config.from_email else "",
        },
        {
            "to": to_email,
            "from_email": config.from_email,
            "from_name": config.from_name or "HawkPhish Test",
            "subject": "HawkPhish Test Email",
            "html_body": "<h1>Test</h1><p>This is a test email from HawkPhish.</p>",
            "text_body": "Test email from HawkPhish",
            "message_id": f"<test@hawkphish>",
            "headers": {},
        },
    )

    if result["success"]:
        config.emails_sent += 1
        await db.commit()

    return {"success": result["success"], "error": result.get("error")}


@router.post("/validate-all")
async def validate_all_smtp(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SMTPConfig))
    configs = result.scalars().all()
    checker = SMTPHealthChecker()
    results = []
    for config in configs:
        r = await checker.check({
            "provider": config.provider, "host": config.host, "port": config.port,
            "username": config.username, "password": config.password,
            "api_key": config.api_key, "use_tls": config.use_tls,
            "domain": config.from_email.split("@")[1] if "@" in config.from_email else "",
        })
        config.is_healthy = r["healthy"]
        config.last_health_check = datetime.utcnow()
        results.append({
            "id": config.id, "name": config.name, "provider": config.provider,
            "healthy": r["healthy"], "latency": r["latency"], "error": r.get("error"),
        })
    await db.commit()
    return results


def _parse_smtp_line(line: str) -> dict:
    """Parse a single SMTP line in various formats:
    - host|user|pass||from_email
    - host|user|pass|from_email
    - host|user|pass
    - host:port:user:pass
    - host:port:user{pass
    - host:user{pass
    - host user pass
    - host, user, pass
    """
    line = line.strip()
    if not line or line.startswith('#'):
        return None

    # Try pipe format: host|user|pass||from or host|user|pass|from or host|user|pass
    if '|' in line:
        parts = [p.strip() for p in line.split('|') if p.strip()]
        if len(parts) >= 3:
            host = parts[0]
            user = parts[1]
            password = parts[2]
            from_email = parts[3] if len(parts) > 3 else user
            port = 587
            tls = True
            if ':' in host:
                hp = host.split(':')
                host = hp[0]
                try:
                    port = int(hp[1])
                    tls = port != 465
                except ValueError:
                    pass
            return {"host": host, "port": port, "username": user, "password": password, "from_email": from_email, "use_tls": tls}

    # Try brace format: host:port:user{pass or host:user{pass
    m = re.match(r'^(.+?):(\d+):(.+?)\{(.+?)$', line)
    if m:
        host, port, user, password = m.group(1), int(m.group(2)), m.group(3), m.group(4)
        return {"host": host, "port": port, "username": user, "password": password, "from_email": user, "use_tls": port != 465}

    m = re.match(r'^(.+?):(.+?)\{(.+?)$', line)
    if m:
        host, user, password = m.group(1), m.group(2), m.group(3)
        port = 587
        if ':' in host:
            hp = host.split(':')
            host = hp[0]
            try:
                port = int(hp[1])
            except ValueError:
                pass
        return {"host": host, "port": port, "username": user, "password": password, "from_email": user, "use_tls": port != 465}

    # Try colon format: host:port:user:pass or host:user:pass
    parts_colon = line.split(':')
    if len(parts_colon) == 4:
        host, port_str, user, password = parts_colon
        try:
            port = int(port_str)
            return {"host": host, "port": port, "username": user, "password": password, "from_email": user, "use_tls": port != 465}
        except ValueError:
            pass
    if len(parts_colon) == 3:
        host, user, password = parts_colon
        if '.' in host or 'localhost' in host:
            return {"host": host, "port": 587, "username": user, "password": password, "from_email": user, "use_tls": True}

    # Try space format: host user pass
    parts_space = line.split()
    if len(parts_space) >= 3:
        return {"host": parts_space[0], "port": 587, "username": parts_space[1], "password": parts_space[2], "from_email": parts_space[1], "use_tls": True}

    # Try comma format: host, user, pass
    parts_comma = [p.strip() for p in line.split(',')]
    if len(parts_comma) >= 3:
        return {"host": parts_comma[0], "port": 587, "username": parts_comma[1], "password": parts_comma[2], "from_email": parts_comma[1], "use_tls": True}

    return None


def _detect_provider(host: str) -> str:
    """Auto-detect provider from hostname"""
    host = host.lower()
    if 'office365' in host or 'outlook' in host:
        return 'office365'
    if 'gmail' in host or 'google' in host:
        return 'gmail'
    if 'sendgrid' in host:
        return 'sendgrid'
    if 'mailgun' in host:
        return 'mailgun'
    if 'postmark' in host:
        return 'postmark'
    if 'sparkpost' in host:
        return 'sparkpost'
    if 'ses' in host or 'amazonaws' in host:
        return 'aws_ses'
    if 'zoho' in host:
        return 'zoho'
    if 'yandex' in host:
        return 'yandex'
    if 'mailtrap' in host:
        return 'mailtrap'
    if 'brevo' in host or 'sendinblue' in host:
        return 'brevo'
    return 'custom'


@router.post("/bulk-import")
async def bulk_import_smtp(data: dict, db: AsyncSession = Depends(get_db)):
    raw = data.get("configs", "")
    if not raw:
        raise HTTPException(400, "No configs provided")

    lines = raw.strip().split('\n')
    imported = 0
    skipped = 0
    errors = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parsed = _parse_smtp_line(line)
        if not parsed:
            skipped += 1
            errors.append(f"Could not parse: {line[:50]}")
            continue

        provider = _detect_provider(parsed["host"])
        name = f"{parsed['host'].split('.')[0].title()} - {parsed['username'][:20]}"

        config = SMTPConfig(
            name=name,
            provider=provider,
            host=parsed["host"],
            port=parsed["port"],
            username=parsed["username"],
            password=parsed["password"],
            from_email=parsed.get("from_email", parsed["username"]),
            from_name="",
            use_tls=parsed["use_tls"],
            max_emails=500,
        )
        db.add(config)
        imported += 1

    await db.commit()
    return {"imported": imported, "skipped": skipped, "errors": errors}
