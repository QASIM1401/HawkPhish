"""HawkPhish - Email Validation Routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from services.email_validation import EmailValidator
from typing import List

router = APIRouter(prefix="/api/validate", tags=["Email Validation"])

@router.get("/email")
async def validate_single_email(
    email: str,
    check_mx: bool = True,
    check_smtp: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Validate a single email address."""
    result = await EmailValidator.validate(email, check_mx=check_mx, check_smtp=check_smtp)
    return result


@router.post("/bulk")
async def validate_bulk_emails(
    emails: List[str],
    check_mx: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """Validate multiple email addresses concurrently."""
    results = await EmailValidator.validate_bulk(emails, check_mx=check_mx)
    return {
        "results": results,
        "total": len(results),
        "valid": sum(1 for r in results if r["valid"]),
        "invalid": sum(1 for r in results if not r["valid"]),
    }


@router.get("/check-disposable")
async def check_disposable(email: str):
    """Check if email uses a disposable domain."""
    result = EmailValidator.check_disposable(email)
    return result


@router.get("/check-role")
async def check_role_based(email: str):
    """Check if email is role-based (admin@, info@, etc.)."""
    result = EmailValidator.check_role_based(email)
    return result
