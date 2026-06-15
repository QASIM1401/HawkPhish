"""HawkPhish - Landing Page Routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import LandingPage
from pydantic import BaseModel
from typing import Optional
from services.landing_templates import get_all_templates, get_template

router = APIRouter(prefix="/api/landing-pages", tags=["Landing Pages"])


class LandingPageCreate(BaseModel):
    name: str
    url: Optional[str] = ""
    html_content: Optional[str] = ""
    capture_credentials: bool = True
    capture_fields: list = ["email", "password"]
    redirect_url: Optional[str] = ""


@router.get("")
async def list_landing_pages(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LandingPage).order_by(LandingPage.created_at.desc()))
    pages = result.scalars().all()
    return [{
        "id": p.id, "name": p.name, "url": p.url,
        "capture_credentials": p.capture_credentials,
        "capture_fields": p.capture_fields,
        "redirect_url": p.redirect_url,
        "created_at": p.created_at.isoformat(),
    } for p in pages]


@router.post("")
async def create_landing_page(data: LandingPageCreate, db: AsyncSession = Depends(get_db)):
    page = LandingPage(**data.model_dump())
    db.add(page)
    await db.commit()
    await db.refresh(page)
    return {"id": page.id, "message": "Landing page created"}


@router.get("/{page_id}")
async def get_landing_page(page_id: int, db: AsyncSession = Depends(get_db)):
    page = await db.get(LandingPage, page_id)
    if not page:
        raise HTTPException(404, "Landing page not found")
    return {
        "id": page.id, "name": page.name, "url": page.url,
        "html_content": page.html_content,
        "capture_credentials": page.capture_credentials,
        "capture_fields": page.capture_fields,
        "redirect_url": page.redirect_url,
        "created_at": page.created_at.isoformat(),
    }


@router.put("/{page_id}")
async def update_landing_page(page_id: int, data: LandingPageCreate, db: AsyncSession = Depends(get_db)):
    page = await db.get(LandingPage, page_id)
    if not page:
        raise HTTPException(404, "Landing page not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(page, k, v)
    await db.commit()
    return {"message": "Landing page updated"}


@router.delete("/{page_id}")
async def delete_landing_page(page_id: int, db: AsyncSession = Depends(get_db)):
    page = await db.get(LandingPage, page_id)
    if not page:
        raise HTTPException(404, "Landing page not found")
    await db.delete(page)
    await db.commit()
    return {"message": "Landing page deleted"}


@router.get("/templates/list")
async def list_prebuilt_templates():
    return get_all_templates()


@router.get("/templates/{template_name}")
async def get_prebuilt_template(template_name: str):
    t = get_template(template_name)
    if not t:
        raise HTTPException(404, "Template not found")
    return t


@router.post("/templates/{template_name}/use")
async def use_prebuilt_template(template_name: str, data: LandingPageCreate, db: AsyncSession = Depends(get_db)):
    t = get_template(template_name)
    if not t:
        raise HTTPException(404, "Template not found")
    page = LandingPage(
        name=data.name or t["name"],
        html_content=t["html"],
        capture_fields=t["capture_fields"],
        **{k: v for k, v in data.model_dump().items() if k not in ("name", "html_content", "capture_fields")}
    )
    db.add(page)
    await db.commit()
    await db.refresh(page)
    return {"id": page.id, "message": f"Landing page created from {t['name']} template"}


@router.post("/import-url")
async def import_from_url(data: dict):
    import httpx
    url = data.get("url", "")
    if not url:
        raise HTTPException(400, "URL required")
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            r = await client.get(url)
            return {"html_content": r.text, "status_code": r.status_code}
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch: {str(e)}")
