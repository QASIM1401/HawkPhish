"""HawkPhish - Email Validation Engine"""
import re
import asyncio
import socket
import smtplib
from typing import Dict, List
from email_validator import validate_email as ev_validate_email, EmailNotValidError


DISPOSABLE_DOMAINS = {
    "tempmail.com", "throwaway.com", "mailinator.com", "guerrillamail.com",
    "yopmail.com", "sharklasers.com", "getairmail.com", "10minutemail.com",
    "burnermail.io", "temp-mail.org", "fakeinbox.com", "mailnesia.com",
    "tempinbox.com", "mailcatch.com", "33mail.com", "getnada.com",
    "inboxalias.com", "mailnesia.com", "tempmailaddress.com", "throwawaymail.com",
}

ROLE_BASED_PREFIXES = {
    "admin", "info", "support", "sales", "marketing", "contact", "help",
    "webmaster", "postmaster", "hostmaster", "abuse", "noc", "security",
    "billing", "legal", "careers", "jobs", "press", "media", "news",
}


def is_disposable(email: str) -> bool:
    domain = email.split("@")[-1].lower()
    return domain in DISPOSABLE_DOMAINS


def get_mx_records(domain: str) -> List[str]:
    """Get MX records for a domain."""
    try:
        import dns.resolver
        answers = dns.resolver.resolve(domain, "MX")
        return sorted([str(r.exchange).rstrip(".") for r in answers], key=lambda x: x[0])
    except Exception:
        return []


async def validate_email_smtp(email: str, timeout: int = 10) -> Dict:
    """Validate email by checking MX records and performing SMTP handshake."""
    domain = email.split("@")[-1]
    mx_records = get_mx_records(domain)
    if not mx_records:
        return {"valid": False, "reason": "No MX records found", "deliverable": False}

    loop = asyncio.get_event_loop()

    def _check():
        try:
            server = smtplib.SMTP(timeout=timeout)
            server.connect(mx_records[0], 25)
            server.ehlo()
            server.mail("test@example.com")
            code, message = server.rcpt(email)
            server.quit()
            return {"valid": code in [250, 251], "reason": f"SMTP code {code}", "deliverable": code in [250, 251]}
        except Exception as e:
            return {"valid": True, "reason": f"SMTP check inconclusive: {str(e)}", "deliverable": None}

    return await loop.run_in_executor(None, _check)


async def validate_email(email: str, check_mx: bool = True, check_smtp: bool = False) -> Dict:
    """Full email validation pipeline."""
    result = {
        "email": email,
        "valid": False,
        "syntax": False,
        "disposable": False,
        "role_based": False,
        "mx_valid": False,
        "deliverable": False,
        "reason": "",
    }

    # Syntax validation
    try:
        ev_validate_email(email)
        result["syntax"] = True
    except EmailNotValidError as e:
        result["reason"] = str(e)
        return result

    # Disposable check
    if is_disposable(email):
        result["disposable"] = True
        result["reason"] = "Disposable email address"
        return result

    # Role-based check
    local_part = email.split("@")[0].lower()
    if local_part in ROLE_BASED_PREFIXES or local_part.startswith(tuple(ROLE_BASED_PREFIXES)):
        result["role_based"] = True

    # MX validation
    if check_mx:
        domain = email.split("@")[-1]
        mx_records = get_mx_records(domain)
        result["mx_valid"] = len(mx_records) > 0
        if not result["mx_valid"]:
            result["reason"] = "No MX records found"
            return result

    # SMTP validation
    if check_smtp and result["mx_valid"]:
        smtp_result = await validate_email_smtp(email)
        result["deliverable"] = smtp_result.get("deliverable", False)
        result["reason"] = smtp_result.get("reason", "")

    if check_mx:
        result["valid"] = result["syntax"] and not result["disposable"] and result["mx_valid"]
    else:
        result["valid"] = result["syntax"] and not result["disposable"]
        result["mx_valid"] = None
    if not result["reason"]:
        result["reason"] = "Email is valid"
    return result


async def validate_emails(emails: List[str], check_mx: bool = True, check_smtp: bool = False) -> List[Dict]:
    tasks = [validate_email(e, check_mx, check_smtp) for e in emails]
    return await asyncio.gather(*tasks)


class EmailValidator:
    """Class-based wrapper for email validation (used by API routes)."""

    @staticmethod
    async def validate(email: str, check_mx: bool = True, check_smtp: bool = False) -> Dict:
        return await validate_email(email, check_mx, check_smtp)

    @staticmethod
    async def validate_bulk(emails: List[str], check_mx: bool = True) -> List[Dict]:
        return await validate_emails(emails, check_mx, check_smtp=False)

    @staticmethod
    def check_disposable(email: str) -> Dict:
        return {"email": email, "disposable": is_disposable(email)}

    @staticmethod
    def check_role_based(email: str) -> Dict:
        local = email.split("@")[0].lower()
        return {"email": email, "role_based": local in ROLE_BASED_PREFIXES}
