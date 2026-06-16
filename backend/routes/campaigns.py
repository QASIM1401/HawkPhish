"""HawkPhish - Campaign Routes"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Campaign, EmailLog, Recipient, SMTPConfig
from services.campaign_service import CampaignManager
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/api/campaigns", tags=["Campaigns"])


class CampaignCreate(BaseModel):
    name: str
    template_id: int
    landing_page_id: Optional[int] = None
    smtp_id: int
    group_id: int
    use_proxies: bool = False
    settings: dict = {}
    subject_rotation: int = 1
    fromname_rotation: int = 1
    letter_rotation: bool = False
    reply_to: Optional[str] = None
    bcc: Optional[str] = None
    cc: Optional[str] = None
    spoof_from: Optional[str] = None
    attachments: list = []
    disclaimer_enabled: bool = False
    custom_headers: dict = {}


@router.get("")
async def list_campaigns(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Campaign).order_by(Campaign.created_at.desc()))
    campaigns = result.scalars().all()
    return [{
        "id": c.id, "name": c.name, "status": c.status,
        "total_sent": c.total_sent, "total_opened": c.total_opened,
        "total_clicked": c.total_clicked, "total_submitted": c.total_submitted,
        "total_bounced": c.total_bounced, "total_failed": c.total_failed,
        "started_at": c.started_at.isoformat() if c.started_at else None,
        "completed_at": c.completed_at.isoformat() if c.completed_at else None,
        "created_at": c.created_at.isoformat(),
    } for c in campaigns]


@router.post("")
async def create_campaign(data: CampaignCreate, db: AsyncSession = Depends(get_db)):
    manager = CampaignManager(db)
    campaign = await manager.create_campaign(data.model_dump())
    return {"id": campaign.id, "message": "Campaign created"}


@router.get("/{campaign_id}")
async def get_campaign(campaign_id: int, db: AsyncSession = Depends(get_db)):
    manager = CampaignManager(db)
    stats = await manager.get_stats(campaign_id)
    if not stats:
        raise HTTPException(404, "Campaign not found")
    return stats


@router.put("/{campaign_id}")
async def update_campaign(campaign_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    if "status" in data:
        campaign.status = data["status"]
    if "name" in data:
        campaign.name = data["name"]
    if "settings" in data:
        campaign.settings = data["settings"]
    await db.commit()
    return {"message": "Campaign updated"}


@router.post("/{campaign_id}/start")
async def start_campaign(campaign_id: int, db: AsyncSession = Depends(get_db)):
    manager = CampaignManager(db)
    result = await manager.start_campaign(campaign_id)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@router.post("/{campaign_id}/pause")
async def pause_campaign(campaign_id: int, db: AsyncSession = Depends(get_db)):
    manager = CampaignManager(db)
    result = await manager.pause_campaign(campaign_id)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@router.post("/{campaign_id}/cancel")
async def cancel_campaign(campaign_id: int, db: AsyncSession = Depends(get_db)):
    manager = CampaignManager(db)
    result = await manager.cancel_campaign(campaign_id)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@router.get("/{campaign_id}/timeline")
async def get_timeline(campaign_id: int, db: AsyncSession = Depends(get_db)):
    manager = CampaignManager(db)
    timeline = await manager.get_timeline(campaign_id)
    return timeline


@router.get("/{campaign_id}/report/pdf")
async def download_campaign_pdf(campaign_id: int, db: AsyncSession = Depends(get_db)):
    from services.report_service import generate_campaign_report
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    result = await db.execute(select(EmailLog).where(EmailLog.campaign_id == campaign_id))
    emails = result.scalars().all()
    email_dicts = []
    for e in emails:
        recipient = await db.get(Recipient, e.recipient_id) if e.recipient_id else None
        email_dicts.append({
            "email": recipient.email if recipient else "",
            "status": e.status,
            "opened_at": e.opened_at.isoformat() if e.opened_at else None,
            "clicked_at": e.clicked_at.isoformat() if e.clicked_at else None,
            "submitted_at": e.submitted_at.isoformat() if e.submitted_at else None,
        })
    campaign_dict = {
        "name": campaign.name,
        "status": campaign.status,
        "total_sent": campaign.total_sent,
        "total_opened": campaign.total_opened,
        "total_clicked": campaign.total_clicked,
        "total_submitted": campaign.total_submitted,
        "total_bounced": campaign.total_bounced,
        "total_failed": campaign.total_failed,
    }
    pdf_bytes = generate_campaign_report(campaign_dict, email_dicts, [])
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={campaign.name}_report.pdf"},
    )


@router.get("/{campaign_id}/report/json")
async def download_campaign_json(campaign_id: int, db: AsyncSession = Depends(get_db)):
    from services.report_service import generate_campaign_report_json
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    result = await db.execute(select(EmailLog).where(EmailLog.campaign_id == campaign_id))
    emails = result.scalars().all()
    email_dicts = []
    for e in emails:
        recipient = await db.get(Recipient, e.recipient_id) if e.recipient_id else None
        email_dicts.append({
            "email": recipient.email if recipient else "",
            "status": e.status,
            "opened_at": e.opened_at.isoformat() if e.opened_at else None,
            "clicked_at": e.clicked_at.isoformat() if e.clicked_at else None,
            "submitted_at": e.submitted_at.isoformat() if e.submitted_at else None,
            "error": e.error_message,
        })
    campaign_dict = {
        "name": campaign.name,
        "status": campaign.status,
        "total_sent": campaign.total_sent,
        "total_opened": campaign.total_opened,
        "total_clicked": campaign.total_clicked,
        "total_submitted": campaign.total_submitted,
        "total_bounced": campaign.total_bounced,
        "total_failed": campaign.total_failed,
    }
    json_str = generate_campaign_report_json(campaign_dict, email_dicts, [])
    return StreamingResponse(
        iter([json_str.encode()]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={campaign.name}_report.json"},
    )


@router.get("/{campaign_id}/report/csv")
async def download_campaign_csv(campaign_id: int, db: AsyncSession = Depends(get_db)):
    from services.report_service import generate_campaign_report_csv
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    result = await db.execute(select(EmailLog).where(EmailLog.campaign_id == campaign_id))
    emails = result.scalars().all()
    email_dicts = []
    for e in emails:
        recipient = await db.get(Recipient, e.recipient_id) if e.recipient_id else None
        email_dicts.append({
            "email": recipient.email if recipient else "",
            "status": e.status,
            "opened_at": e.opened_at.isoformat() if e.opened_at else None,
            "clicked_at": e.clicked_at.isoformat() if e.clicked_at else None,
            "submitted_at": e.submitted_at.isoformat() if e.submitted_at else None,
            "error": e.error_message,
        })
    smtp_config = await db.get(SMTPConfig, campaign.smtp_id) if campaign.smtp_id else None
    campaign_dict = {
        "name": campaign.name,
        "from_email": smtp_config.from_email if smtp_config else "",
    }
    csv_str = generate_campaign_report_csv(campaign_dict, email_dicts)
    return StreamingResponse(
        iter([csv_str.encode()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={campaign.name}_report.csv"},
    )


@router.get("/report/pdf/summary")
async def download_summary_pdf(db: AsyncSession = Depends(get_db)):
    from services.report_service import generate_dashboard_summary
    result = await db.execute(select(Campaign).order_by(Campaign.created_at.desc()))
    campaigns = result.scalars().all()
    campaign_dicts = [{
        "name": c.name, "status": c.status,
        "total_sent": c.total_sent, "total_opened": c.total_opened,
        "total_clicked": c.total_clicked, "total_submitted": c.total_submitted,
    } for c in campaigns]
    pdf_bytes = generate_dashboard_summary(campaign_dicts)
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=dashboard_summary.pdf"},
    )


@router.delete("/{campaign_id}")
async def delete_campaign(campaign_id: int, db: AsyncSession = Depends(get_db)):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    await db.delete(campaign)
    await db.commit()
    return {"message": "Campaign deleted"}
