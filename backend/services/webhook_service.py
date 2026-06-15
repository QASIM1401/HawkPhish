"""HawkPhish - Webhook Notifications"""
import json
import hmac
import hashlib
import httpx
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Webhook


EVENT_NAMES = {
    "open": "Email Opened",
    "click": "Link Clicked",
    "submit": "Credentials Submitted",
    "campaign_start": "Campaign Started",
    "campaign_pause": "Campaign Paused",
    "campaign_complete": "Campaign Completed",
}


def _format_slack(event: str, data: dict) -> dict:
    color_map = {"open": "#36a64f", "click": "#2196F3", "submit": "#f44336", "campaign_start": "#ff9800"}
    return {
        "attachments": [{
            "color": color_map.get(event, "#999999"),
            "title": f"HawkPhish: {EVENT_NAMES.get(event, event)}",
            "fields": [
                {"title": "Campaign", "value": data.get("campaign_name", "Unknown"), "short": True},
                {"title": "Recipient", "value": data.get("email", "Unknown"), "short": True},
                {"title": "IP", "value": data.get("ip_address", "Unknown"), "short": True},
                {"title": "Time", "value": datetime.utcnow().isoformat(), "short": True},
            ],
            "footer": "HawkPhish",
        }]
    }


def _format_discord(event: str, data: dict) -> dict:
    color_map = {"open": 3066993, "click": 3447003, "submit": 15158332, "campaign_start": 16776960}
    return {
        "embeds": [{
            "title": f"HawkPhish: {EVENT_NAMES.get(event, event)}",
            "color": color_map.get(event, 0),
            "fields": [
                {"name": "Campaign", "value": data.get("campaign_name", "Unknown"), "inline": True},
                {"name": "Recipient", "value": data.get("email", "Unknown"), "inline": True},
                {"name": "IP", "value": data.get("ip_address", "Unknown"), "inline": True},
                {"name": "Time", "value": datetime.utcnow().isoformat(), "inline": True},
            ],
        }]
    }


def _format_generic(event: str, data: dict) -> dict:
    return {
        "event": event,
        "event_name": EVENT_NAMES.get(event, event),
        "timestamp": datetime.utcnow().isoformat(),
        "data": data,
    }


def _sign_payload(payload: str, secret: str) -> str:
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


async def trigger_webhooks(db: AsyncSession, event: str, data: dict):
    """Trigger all active webhooks for a given event."""
    result = await db.execute(select(Webhook).where(Webhook.is_active == True))
    webhooks = result.scalars().all()

    payload_obj = None
    for webhook in webhooks:
        if webhook.events and event not in webhook.events:
            continue

        # Build payload based on provider
        if webhook.provider == "slack":
            payload_obj = _format_slack(event, data)
        elif webhook.provider == "discord":
            payload_obj = _format_discord(event, data)
        else:
            payload_obj = _format_generic(event, data)

        payload_str = json.dumps(payload_obj)
        headers = {"Content-Type": "application/json"}
        if webhook.secret:
            headers["X-HawkPhish-Signature"] = _sign_payload(payload_str, webhook.secret)

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(webhook.url, json=payload_obj, headers=headers)
        except Exception:
            pass  # Webhooks should not break main flow
