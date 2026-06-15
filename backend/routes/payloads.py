"""HawkPhish - Payload Delivery Routes"""
import os
import secrets
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Payload
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/api/payloads", tags=["Payloads"])

PAYLOAD_DIR = Path(os.path.dirname(__file__)).parent / "payloads"
PAYLOAD_DIR.mkdir(exist_ok=True)


@router.get("")
async def list_payloads(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Payload).order_by(Payload.created_at.desc()))
    payloads = result.scalars().all()
    return [{
        "id": p.id, "name": p.name, "filename": p.filename,
        "content_type": p.content_type, "size": p.size,
        "tracking_token": p.tracking_token, "download_count": p.download_count,
        "created_at": p.created_at.isoformat(),
    } for p in payloads]


@router.post("/upload")
async def upload_payload(
    file: UploadFile = File(...),
    name: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    payload_name = name or (file.filename or "payload")
    token = secrets.token_urlsafe(24)
    safe_filename = Path(file.filename).name
    dest = PAYLOAD_DIR / f"{token}_{safe_filename}"
    content = await file.read()
    dest.write_bytes(content)

    payload = Payload(
        name=payload_name,
        filename=safe_filename,
        content_type=file.content_type or "application/octet-stream",
        size=len(content),
        tracking_token=token,
    )
    db.add(payload)
    await db.commit()
    await db.refresh(payload)
    return {
        "id": payload.id, "name": payload_name, "tracking_token": token,
        "download_url": f"/payloads/{token}/download"
    }


@router.get("/{token}/download")
async def download_payload(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Payload).where(Payload.tracking_token == token))
    payload = result.scalar_one_or_none()
    if not payload:
        raise HTTPException(404, "Payload not found")

    payload.download_count += 1
    await db.commit()

    file_path = PAYLOAD_DIR / f"{payload.tracking_token}_{payload.filename}"
    if not file_path.exists():
        raise HTTPException(404, "File not found")

    return FileResponse(
        str(file_path),
        media_type=payload.content_type,
        filename=payload.filename,
    )


@router.delete("/{payload_id}")
async def delete_payload(payload_id: int, db: AsyncSession = Depends(get_db)):
    payload = await db.get(Payload, payload_id)
    if not payload:
        raise HTTPException(404, "Payload not found")
    file_path = PAYLOAD_DIR / f"{payload.tracking_token}_{payload.filename}"
    if file_path.exists():
        file_path.unlink()
    await db.delete(payload)
    await db.commit()
    return {"message": "Payload deleted"}
