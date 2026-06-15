"""HawkPhish - Audit Logging Service"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import AuditLog
from datetime import datetime
from typing import Optional, List
import json


async def log_action(
    db: AsyncSession,
    action: str,
    entity_type: str = None,
    entity_id: int = None,
    user: str = "system",
    details: dict = None,
    ip_address: str = None,
    success: bool = True,
):
    """Log an action to the audit log"""
    log = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user=user,
        details=details or {},
        ip_address=ip_address,
        success=success,
    )
    db.add(log)
    await db.commit()
    return log


async def get_audit_logs(
    db: AsyncSession,
    action: str = None,
    entity_type: str = None,
    limit: int = 100,
    offset: int = 0,
) -> List[AuditLog]:
    """Get audit logs with optional filters"""
    query = select(AuditLog).order_by(AuditLog.timestamp.desc())
    if action:
        query = query.where(AuditLog.action == action)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def get_audit_log_stats(db: AsyncSession) -> dict:
    """Get audit log statistics"""
    from sqlalchemy import func
    
    total = await db.execute(select(func.count(AuditLog.id)))
    total_count = total.scalar()
    
    success = await db.execute(select(func.count(AuditLog.id)).where(AuditLog.success == True))
    success_count = success.scalar()
    
    failed = await db.execute(select(func.count(AuditLog.id)).where(AuditLog.success == False))
    failed_count = failed.scalar()
    
    # Get action counts
    action_counts = await db.execute(
        select(AuditLog.action, func.count(AuditLog.id))
        .group_by(AuditLog.action)
        .order_by(func.count(AuditLog.id).desc())
    )
    
    return {
        "total": total_count,
        "success": success_count,
        "failed": failed_count,
        "actions": {action: count for action, count in action_counts.all()},
    }
