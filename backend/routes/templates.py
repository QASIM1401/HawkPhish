"""HawkPhish - Template Routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import EmailTemplate
from services.template_engine import TemplateEngine
from services.email_templates import get_all_email_templates, get_email_template
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/templates", tags=["Templates"])
engine = TemplateEngine()


class TemplateCreate(BaseModel):
    name: str
    subject: str
    html_body: str
    text_body: Optional[str] = ""
    category: str = "general"
    severity: str = "Medium"
    tags: list = []


@router.get("")
async def list_templates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EmailTemplate).order_by(EmailTemplate.created_at.desc()))
    templates = result.scalars().all()
    return [{
        "id": t.id, "name": t.name, "subject": t.subject,
        "category": t.category, "severity": t.severity, "tags": t.tags or [],
        "variables": engine.extract_variables(t.subject + t.html_body),
        "created_at": t.created_at.isoformat(), "updated_at": t.updated_at.isoformat(),
    } for t in templates]


@router.post("")
async def create_template(data: TemplateCreate, db: AsyncSession = Depends(get_db)):
    template = EmailTemplate(**data.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return {"id": template.id, "message": "Template created"}


@router.get("/{template_id}")
async def get_template(template_id: int, db: AsyncSession = Depends(get_db)):
    template = await db.get(EmailTemplate, template_id)
    if not template:
        raise HTTPException(404, "Template not found")
    return {
        "id": template.id, "name": template.name, "subject": template.subject,
        "html_body": template.html_body, "text_body": template.text_body,
        "category": template.category,
        "variables": engine.extract_variables(template.subject + template.html_body),
        "created_at": template.created_at.isoformat(),
    }


@router.put("/{template_id}")
async def update_template(template_id: int, data: TemplateCreate, db: AsyncSession = Depends(get_db)):
    template = await db.get(EmailTemplate, template_id)
    if not template:
        raise HTTPException(404, "Template not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(template, k, v)
    await db.commit()
    return {"message": "Template updated"}


@router.delete("/{template_id}")
async def delete_template(template_id: int, db: AsyncSession = Depends(get_db)):
    template = await db.get(EmailTemplate, template_id)
    if not template:
        raise HTTPException(404, "Template not found")
    await db.delete(template)
    await db.commit()
    return {"message": "Template deleted"}


@router.post("/preview")
async def preview_template(data: TemplateCreate):
    rendered = engine.preview(data.subject, data.html_body, data.text_body or "")
    return rendered


@router.get("/prebuilt/list")
async def list_prebuilt_email_templates():
    return get_all_email_templates()


@router.get("/prebuilt/{template_name}")
async def get_prebuilt_email_template(template_name: str):
    t = get_email_template(template_name)
    if not t:
        raise HTTPException(404, "Template not found")
    return t


@router.post("/prebuilt/{template_name}/use")
async def use_prebuilt_email_template(template_name: str, db: AsyncSession = Depends(get_db)):
    t = get_email_template(template_name)
    if not t:
        raise HTTPException(404, "Template not found")
    template = EmailTemplate(
        name=t["name"],
        subject=t["subject"],
        html_body=t["html"],
        category=t["category"],
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return {"id": template.id, "message": f"Template '{t['name']}' created"}
