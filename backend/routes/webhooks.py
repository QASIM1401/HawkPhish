"""HawkPhish - Webhook Routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Webhook
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])


class WebhookCreate(BaseModel):
    name: str
    url: str
    provider: str = "generic"
    events: List[str] = ["open", "click", "submit"]
    secret: Optional[str] = None
    is_active: bool = True


@router.get("")
async def list_webhooks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Webhook).order_by(Webhook.created_at.desc()))
    hooks = result.scalars().all()
    return [{
        "id": h.id, "name": h.name, "url": h.url, "provider": h.provider,
        "events": h.events or [], "is_active": h.is_active,
        "created_at": h.created_at.isoformat(),
    } for h in hooks]


@router.post("")
async def create_webhook(data: WebhookCreate, db: AsyncSession = Depends(get_db)):
    hook = Webhook(**data.model_dump())
    db.add(hook)
    await db.commit()
    await db.refresh(hook)
    return {"id": hook.id, "message": "Webhook created"}


@router.get("/{hook_id}")
async def get_webhook(hook_id: int, db: AsyncSession = Depends(get_db)):
    hook = await db.get(Webhook, hook_id)
    if not hook:
        raise HTTPException(404, "Webhook not found")
    return {
        "id": hook.id, "name": hook.name, "url": hook.url, "provider": hook.provider,
        "events": hook.events or [], "is_active": hook.is_active,
        "created_at": hook.created_at.isoformat(),
    }


@router.put("/{hook_id}")
async def update_webhook(hook_id: int, data: WebhookCreate, db: AsyncSession = Depends(get_db)):
    hook = await db.get(Webhook, hook_id)
    if not hook:
        raise HTTPException(404, "Webhook not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(hook, k, v)
    await db.commit()
    return {"message": "Webhook updated"}


@router.delete("/{hook_id}")
async def delete_webhook(hook_id: int, db: AsyncSession = Depends(get_db)):
    hook = await db.get(Webhook, hook_id)
    if not hook:
        raise HTTPException(404, "Webhook not found")
    await db.delete(hook)
    await db.commit()
    return {"message": "Webhook deleted"}
