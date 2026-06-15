"""HawkPhish - Analytics Routes"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from services.analytics_service import AnalyticsService
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/heatmap")
async def get_heatmap(
    campaign_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get geolocation heatmap data for campaigns."""
    data = await AnalyticsService.get_geolocation_heatmap(db, campaign_id)
    return data


@router.get("/time-to-click")
async def get_time_to_click(
    campaign_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get time-to-click analytics (average time between sent and click/open)."""
    data = await AnalyticsService.get_time_to_click_analytics(db, campaign_id)
    return data


@router.get("/repeat-victims")
async def get_repeat_victims(
    min_campaigns: int = Query(2, ge=2),
    db: AsyncSession = Depends(get_db),
):
    """Detect recipients who fell for multiple campaigns."""
    data = await AnalyticsService.get_repeat_victim_detection(db, min_campaigns)
    return data


@router.get("/campaigns/filter")
async def filter_campaigns(
    status: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    template_id: Optional[int] = Query(None),
    group_id: Optional[int] = Query(None),
    smtp_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Advanced campaign filtering by status, date range, template, group, or SMTP."""
    filters = {
        "status": status,
        "date_from": date_from,
        "date_to": date_to,
        "template_id": template_id,
        "group_id": group_id,
        "smtp_id": smtp_id,
    }
    filters = {k: v for k, v in filters.items() if v is not None}
    campaigns = await AnalyticsService.get_advanced_campaign_filters(db, filters)
    return [{
        "id": c.id, "name": c.name, "status": c.status,
        "total_sent": c.total_sent, "total_opened": c.total_opened,
        "total_clicked": c.total_clicked, "total_submitted": c.total_submitted,
        "created_at": c.created_at.isoformat(),
    } for c in campaigns]
