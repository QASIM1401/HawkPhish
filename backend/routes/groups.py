"""HawkPhish - Group & Recipient Routes"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Group, Recipient
from pydantic import BaseModel
from typing import Optional, List
import csv
import io

router = APIRouter(prefix="/api/groups", tags=["Groups"])


class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    color: str = "#3B82F6"


class RecipientCreate(BaseModel):
    email: str
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    position: Optional[str] = ""
    custom_data: dict = {}


@router.get("")
async def list_groups(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Group))
    groups = result.scalars().all()
    output = []
    for g in groups:
        count = await db.execute(select(Recipient).where(Recipient.group_id == g.id))
        output.append({
            "id": g.id, "name": g.name, "description": g.description,
            "color": g.color, "recipient_count": len(count.scalars().all()),
            "created_at": g.created_at.isoformat(),
        })
    return output


@router.post("")
async def create_group(data: GroupCreate, db: AsyncSession = Depends(get_db)):
    group = Group(**data.model_dump())
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return {"id": group.id, "message": "Group created"}


@router.get("/{group_id}")
async def get_group(group_id: int, db: AsyncSession = Depends(get_db)):
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(404, "Group not found")
    count = await db.execute(select(Recipient).where(Recipient.group_id == group_id))
    return {
        "id": group.id, "name": group.name, "description": group.description,
        "color": group.color, "recipient_count": len(count.scalars().all()),
        "created_at": group.created_at.isoformat(),
    }


@router.put("/{group_id}")
async def update_group(group_id: int, data: GroupCreate, db: AsyncSession = Depends(get_db)):
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(404, "Group not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(group, k, v)
    await db.commit()
    return {"message": "Group updated"}


@router.delete("/{group_id}")
async def delete_group(group_id: int, db: AsyncSession = Depends(get_db)):
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(404, "Group not found")
    await db.delete(group)
    await db.commit()
    return {"message": "Group deleted"}


@router.get("/{group_id}/recipients")
async def list_recipients(group_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Recipient).where(Recipient.group_id == group_id))
    recipients = result.scalars().all()
    return [{
        "id": r.id, "email": r.email, "first_name": r.first_name,
        "last_name": r.last_name, "position": r.position,
        "created_at": r.created_at.isoformat(),
    } for r in recipients]


@router.post("/{group_id}/recipients")
async def add_recipient(group_id: int, data: RecipientCreate, db: AsyncSession = Depends(get_db)):
    recipient = Recipient(group_id=group_id, **data.model_dump())
    db.add(recipient)
    await db.commit()
    return {"message": "Recipient added"}


@router.post("/{group_id}/recipients/import")
async def import_recipients(group_id: int, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    content = await file.read()
    text = content.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))

    count = 0
    for row in reader:
        email = row.get("email", "").strip()
        if not email or "@" not in email:
            continue
        recipient = Recipient(
            group_id=group_id,
            email=email,
            first_name=row.get("first_name", row.get("firstName", "")),
            last_name=row.get("last_name", row.get("lastName", "")),
            position=row.get("position", row.get("title", "")),
        )
        db.add(recipient)
        count += 1

    await db.commit()
    return {"message": f"Imported {count} recipients"}


@router.delete("/{group_id}/recipients/{recipient_id}")
async def delete_recipient(group_id: int, recipient_id: int, db: AsyncSession = Depends(get_db)):
    recipient = await db.get(Recipient, recipient_id)
    if not recipient or recipient.group_id != group_id:
        raise HTTPException(404, "Recipient not found")
    await db.delete(recipient)
    await db.commit()
    return {"message": "Recipient deleted"}
