"""HawkPhish - Audit Log Routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from services.audit_log_service import get_audit_logs, get_audit_log_stats

router = APIRouter(prefix="/api/audit-logs", tags=["Audit Logs"])


@router.get("")
async def list_audit_logs(
    action: str = None,
    entity_type: str = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    logs = await get_audit_logs(db, action, entity_type, limit, offset)
    return {
        "logs": [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "user": log.user,
                "details": log.details,
                "ip_address": log.ip_address,
                "success": log.success,
            }
            for log in logs
        ],
        "total": len(logs),
    }


@router.get("/stats")
async def audit_stats(db: AsyncSession = Depends(get_db)):
    return await get_audit_log_stats(db)
