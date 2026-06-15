"""HawkPhish - SMTP Manager (All Providers)"""
import smtplib
import ssl
import socket
import json
import asyncio
import time
import random
import logging
import os
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import httpx
import hashlib

logger = logging.getLogger("hawkphish.smtp")

# ── sender.py quality helpers ──────────────────────────────────

EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def validate_email(email: str) -> bool:
    return bool(email) and EMAIL_RE.match(email) is not None

def generate_message_id(domain: str) -> str:
    from email.utils import make_msgid
    return make_msgid(domain=domain)

def create_spf_header(domain: str) -> str:
    return f"v=spf1 include:_spf.{domain} ~all"

def create_dkim_signature(domain: str, selector: str = "default") -> str:
    # Simulated DKIM signature (enhances deliverability appearance)
    headers = ['from', 'to', 'subject', 'date', 'message-id']
    return f"v=1; a=rsa-sha256; d={domain}; s={selector}; h={':'.join(headers)}; bh=abc123; b=def456"

def add_senderpy_headers(msg: MIMEMultipart, domain: str, username: str, spoof_from: str = None):
    """Full sender.py authentication header injection for maximum deliverability."""
    # Message-ID
    msg['Message-ID'] = generate_message_id(domain)
    # Authentication-Results
    msg['Authentication-Results'] = f"{domain}; spf=pass smtp.mailfrom={username}; dkim=pass header.d={domain}; dmarc=pass"
    # SPF
    msg['Received-SPF'] = f"pass ({domain}: domain of {username} designates {socket.gethostbyname(socket.gethostname())} as permitted sender)"
    # DKIM
    msg['DKIM-Signature'] = create_dkim_signature(domain)
    # DMARC
    msg['DMARC-Filter'] = "Pass"
    # Real IP headers
    try:
        real_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        real_ip = "127.0.0.1"
    msg['X-Originating-IP'] = real_ip
    msg['X-Forwarded-For'] = real_ip
    msg['X-Real-IP'] = real_ip
    # Anti-spam headers
    msg['X-Spam-Status'] = "No, score=0.0"
    msg['X-Spam-Level'] = ""
    msg['X-Spam-Checker-Version'] = "SpamAssassin 3.4.0"
    # Email client headers (Microsoft Outlook)
    msg['X-Mailer'] = 'Microsoft Outlook 16.0'
    msg['X-MimeOLE'] = 'Produced By Microsoft MimeOLE V6.00.2800.1441'
    msg['X-MS-Exchange-Organization-AuthAs'] = 'Internal'
    msg['X-MS-Exchange-Organization-AuthSource'] = 'Office365'
    msg['X-MS-Exchange-Organization-BypassClutter'] = 'true'
    # Priority
    msg['X-Priority'] = '3'
    msg['X-MSMail-Priority'] = 'Normal'
    msg['Importance'] = 'Normal'
    # List management
    msg['List-Unsubscribe'] = f'<mailto:unsubscribe@{domain}>, <https://{domain}/unsubscribe>'
    msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
    # Return path
    msg['Return-Path'] = username
    # Spoof tracking
    if spoof_from:
        msg['X-Spoof'] = spoof_from
    # Content headers
    msg['MIME-Version'] = '1.0'
    msg['Content-Type'] = 'text/html; charset=UTF-8'
    msg['Content-Transfer-Encoding'] = '8bit'

def clean_smtp_configs(raw_lines: list[str]) -> tuple[list[dict], list[str]]:
    """sender.py quality SMTP cleaning: validate, deduplicate, filter bad entries."""
    valid = []
    errors = []
    seen = set()
    for line in raw_lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.count('|') != 3:
            errors.append(f"Bad format: {line[:50]}")
            continue
        host, port_str, username, password = line.split('|')
        if not all([host, port_str, username, password]):
            errors.append(f"Empty field: {line[:50]}")
            continue
        if any(k in part for part in [host, port_str, username, password] for k in ['***', 'null', 'localhost']):
            errors.append(f"Bad token: {line[:50]}")
            continue
        try:
            port = int(port_str)
            if not (1 <= port <= 65535):
                errors.append(f"Bad port: {line[:50]}")
                continue
        except ValueError:
            errors.append(f"Non-numeric port: {line[:50]}")
            continue
        key = f"{host}|{port}|{username}|{password}"
        if key in seen:
            errors.append(f"Duplicate: {line[:50]}")
            continue
        seen.add(key)
        valid.append({"host": host, "port": port, "username": username, "password": password, "line": line})
    return valid, errors


def _make_tls_context():
    """Create TLS context that forces TLS 1.2+ (required by Office365, Gmail, etc.)"""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    return ctx


class SMTPHealthChecker:
    """Check SMTP connection health"""

    PROVIDER_HOSTS = {
        "office365": ("smtp.office365.com", 587),
        "gmail": ("smtp.gmail.com", 587),
        "outlook": ("smtp-mail.outlook.com", 587),
        "sendgrid": ("smtp.sendgrid.net", 587),
        "mailgun": ("smtp.mailgun.org", 587),
        "postmark": ("smtp.postmarkapp.com", 587),
        "sparkpost": ("smtp.sparkpostmail.com", 587),
        "aws_ses": ("email-smtp.us-east-1.amazonaws.com", 465),
        "zoho": ("smtp.zoho.com", 587),
        "zohomail": ("smtp.zoho.com", 587),
        "yandex": ("smtp.yandex.com", 465),
        "mailtrap": ("smtp.mailtrap.io", 587),
        " Brevo": ("smtp-relay.brevo.com", 587),
        "mailchimp": ("smtp.mailchimp.com", 587),
        "turbo smtp": ("smtp.turbo-smtp.com", 587),
        "one_com": ("send.one.com", 465),
        "godaddy": ("smtpout.secureserver.net", 465),
        "ics_cool": ("mail.icsCoolEmail.com", 587),
        "hexamail": ("smtp.hexamail.com", 587),
        "ionos": ("smtp.ionos.com", 587),
        "namecheap": ("mail.namecheap.com", 465),
        "hostgator": ("mail.hostgator.com", 465),
        "bluehost": ("mail.bluehost.com", 465),
        "siteground": ("mail.siteground.com", 465),
        "google_workspace": ("smtp.google.com", 587),
        "microsoft_365": ("smtp.office365.com", 587),
        " Mimecast": ("mimecast-smtp-out.qualys.com", 587),
        " proofpoint": ("smtp-us.ppe-hosted.com", 587),
    }

    API_PROVIDERS = ["sendgrid", "mailgun", "postmark", "sparkpost", "mailchimp"]

    @staticmethod
    async def check(config: dict) -> dict:
        result = {"healthy": False, "latency": 0, "error": None}
        start = time.time()

        try:
            if config.get("provider") in SMTPHealthChecker.API_PROVIDERS:
                result = await SMTPHealthChecker._check_api(config)
            else:
                result = await SMTPHealthChecker._check_smtp(config)
        except Exception as e:
            result["error"] = str(e)

        result["latency"] = round((time.time() - start) * 1000)
        return result

    @staticmethod
    async def _check_smtp(config: dict) -> dict:
        import socket
        provider = config.get("provider", "custom")
        host = config.get("host")
        port = config.get("port", 587)

        if not host and provider in SMTPHealthChecker.PROVIDER_HOSTS:
            host, port = SMTPHealthChecker.PROVIDER_HOSTS[provider]

        if not host:
            return {"healthy": False, "error": "No SMTP host configured", "latency": 0}

        username = config.get("username")
        password = config.get("password")
        use_tls = config.get("use_tls", True)

        loop = asyncio.get_event_loop()
        def _test():
            try:
                if use_tls:
                    context = _make_tls_context()
                    with smtplib.SMTP(host, port, timeout=15) as server:
                        server.ehlo()
                        server.starttls(context=context)
                        server.ehlo()
                        server.login(username, password)
                else:
                    with smtplib.SMTP_SSL(host, port, timeout=15, context=context) as server:
                        server.ehlo()
                        server.login(username, password)
                return {"healthy": True, "error": None}
            except smtplib.SMTPAuthenticationError as e:
                msg = e.smtp_error.decode() if isinstance(e.smtp_error, bytes) else str(e.smtp_error)
                return {"healthy": False, "error": f"Auth failed ({e.smtp_code}): {msg}"}
            except smtplib.SMTPConnectError as e:
                msg = e.smtp_error.decode() if isinstance(e.smtp_error, bytes) else str(e.smtp_error)
                return {"healthy": False, "error": f"Connect failed: {msg}"}
            except smtplib.SMTPException as e:
                return {"healthy": False, "error": f"SMTP error: {str(e)}"}
            except ConnectionRefusedError:
                return {"healthy": False, "error": f"Connection refused by {host}:{port}"}
            except socket.gaierror:
                return {"healthy": False, "error": f"DNS failed: cannot resolve {host}"}
            except socket.timeout:
                return {"healthy": False, "error": f"Timeout connecting to {host}:{port}"}
            except OSError as e:
                return {"healthy": False, "error": f"Network error: {str(e)}"}
            except Exception as e:
                return {"healthy": False, "error": f"{type(e).__name__}: {str(e)}"}

        result = await loop.run_in_executor(None, _test)
        return result

    @staticmethod
    async def _check_api(config: dict) -> dict:
        provider = config.get("provider")
        api_key = config.get("api_key")

        async with httpx.AsyncClient(timeout=10) as client:
            if provider == "sendgrid":
                r = await client.get(
                    "https://api.sendgrid.com/v3/user/profile",
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                return {"healthy": r.status_code == 200, "error": None if r.status_code == 200 else r.text}

            elif provider == "mailgun":
                r = await client.get(
                    f"https://api.mailgun.net/v3/{config.get('domain')}/bounce",
                    auth=("api", api_key)
                )
                return {"healthy": r.status_code == 200, "error": None}

            elif provider == "postmark":
                r = await client.get(
                    "https://api.postmarkapp.com/stats/outbound",
                    headers={"Accept": "application/json", "X-Postmark-Server-Token": api_key}
                )
                return {"healthy": r.status_code == 200, "error": None}

            elif provider == "sparkpost":
                r = await client.get(
                    "https://api.sparkpost.com/api/v1/transmissions",
                    headers={"Authorization": api_key, "Accept": "application/json"}
                )
                return {"healthy": r.status_code == 200, "error": None}

        return {"healthy": False, "error": "Unknown API provider"}


class SMTPSender:
    """Send emails through various SMTP providers"""

    def __init__(self):
        self.health_checker = SMTPHealthChecker()

    async def send(self, config: dict, email_data: dict, attachments: list = None, proxy: dict = None) -> dict:
        provider = config.get("provider", "custom")

        try:
            if provider in SMTPHealthChecker.API_PROVIDERS:
                return await self._send_api(config, email_data, attachments)
            else:
                return await self._send_smtp(config, email_data, attachments, proxy=proxy)
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _send_smtp(self, config: dict, email_data: dict, attachments: list = None, proxy: dict = None) -> dict:
        provider = config.get("provider", "custom")
        host = config.get("host")
        port = config.get("port", 587)

        if not host and provider in SMTPHealthChecker.PROVIDER_HOSTS:
            host, port = SMTPHealthChecker.PROVIDER_HOSTS[provider]

        if not host:
            return {"success": False, "error": "No SMTP host configured"}

        username = config.get("username")
        password = config.get("password")
        use_tls = config.get("use_tls", True)

        # Validate recipient email
        to_email = email_data["to"]
        if not validate_email(to_email):
            return {"success": False, "error": f"Invalid email address: {to_email}"}

        # Build proper MIME structure
        has_attachments = attachments and len(attachments) > 0
        if has_attachments:
            msg = MIMEMultipart("mixed")
            alt_part = MIMEMultipart("alternative")
        else:
            msg = MIMEMultipart("alternative")
            alt_part = msg

        # From address: use spoof if available
        from_email = email_data.get("from_email", "")
        from_name = email_data.get("from_name", "")
        spoof_from = email_data.get("spoof_from", "")
        actual_from = spoof_from or from_email

        msg["From"] = f"{from_name} <{actual_from}>"
        msg["To"] = to_email
        msg["Subject"] = email_data["subject"]
        msg["Date"] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S %z')

        # Extract domain for authentication headers
        domain = email_data.get("domain", actual_from.split("@")[1] if "@" in actual_from else "localhost")
        real_username = email_data.get("real_username", username or actual_from)

        # Add full sender.py authentication headers
        add_senderpy_headers(msg, domain, real_username, spoof_from=spoof_from)

        # Reply-To, BCC, CC
        if email_data.get("reply_to"):
            msg["Reply-To"] = email_data["reply_to"]
        if email_data.get("cc"):
            msg["Cc"] = email_data["cc"]
        if email_data.get("bcc"):
            msg["Bcc"] = email_data["bcc"]

        # Custom headers (user-defined, override defaults)
        for key, value in email_data.get("headers", {}).items():
            if key.lower() not in ["from", "to", "subject", "message-id", "date"]:
                msg[key] = value

        # Plain text fallback
        if email_data.get("text_body"):
            alt_part.attach(MIMEText(email_data["text_body"], "plain", "utf-8"))
        alt_part.attach(MIMEText(email_data.get("html_body", ""), "html", "utf-8"))

        if has_attachments:
            msg.attach(alt_part)
            for att in attachments:
                try:
                    filepath = att.get("path") or att.get("filename")
                    if not filepath:
                        continue
                    # Skip HTML file attachments (sender.py pattern)
                    if filepath.lower().endswith(('.html', '.htm')):
                        logger.warning(f"Skipping HTML attachment to avoid duplication: {filepath}")
                        continue
                    if not os.path.isfile(filepath):
                        logger.warning(f"Attachment not found: {filepath}")
                        continue
                    with open(filepath, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                    encoders.encode_base64(part)
                    filename = os.path.basename(filepath)
                    part.add_header("Content-Disposition", f"attachment; filename={filename}")
                    part.add_header("Content-Type", "application/octet-stream")
                    msg.attach(part)
                except Exception as exc:
                    logger.warning(f"Failed to attach {att}: {exc}")

        loop = asyncio.get_event_loop()
        def _send():
            try:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                if proxy:
                    import socks
                    ptype = proxy.get("proxy_type", "http")
                    ptype_map = {"socks5": socks.SOCKS5, "socks4": socks.SOCKS4, "http": socks.HTTP, "https": socks.HTTP}
                    s = socks.socksocket()
                    s.set_proxy(ptype_map.get(ptype, socks.HTTP), proxy["host"], proxy["port"],
                               username=proxy.get("username") or None, password=proxy.get("password") or None)
                    s.settimeout(30)
                    s.connect((host, port))
                    if use_tls:
                        wrapped = context.wrap_socket(s, server_hostname=host)
                        server = smtplib.SMTP(host, port, timeout=30)
                        server.sock = wrapped
                        server.ehlo()
                    else:
                        server = smtplib.SMTP_SSL(host, port, timeout=30, context=context)
                        server.sock = s
                        server.ehlo()
                    server.login(username, password)
                    server.send_message(msg)
                    server.quit()
                elif use_tls:
                    with smtplib.SMTP(host, port, timeout=30) as server:
                        server.ehlo()
                        server.starttls(context=context)
                        server.ehlo()
                        server.login(username, password)
                        server.send_message(msg)
                else:
                    with smtplib.SMTP_SSL(host, port, timeout=30, context=context) as server:
                        server.ehlo()
                        server.login(username, password)
                        server.send_message(msg)
                return {"success": True, "error": None}
            except smtplib.SMTPAuthenticationError as e:
                return {"success": False, "error": f"Authentication failed: {e.smtp_code} {e.smtp_error.decode() if isinstance(e.smtp_error, bytes) else e.smtp_error}"}
            except smtplib.SMTPConnectError as e:
                return {"success": False, "error": f"Connection failed: {e.smtp_code} {e.smtp_error.decode() if isinstance(e.smtp_error, bytes) else e.smtp_error}"}
            except smtplib.SMTPException as e:
                return {"success": False, "error": f"SMTP error: {str(e)}"}
            except ConnectionRefusedError:
                return {"success": False, "error": f"Connection refused by {host}:{port}. Check if the server is reachable."}
            except socket.gaierror:
                return {"success": False, "error": f"DNS resolution failed for {host}. Check the hostname."}
            except socket.timeout:
                return {"success": False, "error": f"Connection timed out to {host}:{port}"}
            except OSError as e:
                return {"success": False, "error": f"Network error: {str(e)}"}
            except Exception as e:
                return {"success": False, "error": f"Unexpected error: {type(e).__name__}: {str(e)}"}

        result = await loop.run_in_executor(None, _send)
        return result

    async def _send_api(self, config: dict, email_data: dict, attachments: list = None) -> dict:
        provider = config.get("provider")
        api_key = config.get("api_key")

        async with httpx.AsyncClient(timeout=30) as client:
            if provider == "sendgrid":
                payload = {
                    "personalizations": [{"to": [{"email": email_data["to"]}]}],
                    "from": {"email": email_data.get("from_email"), "name": email_data.get("from_name", "")},
                    "subject": email_data["subject"],
                    "content": [{"type": "text/html", "value": email_data.get("html_body", "")}],
                    "headers": email_data.get("headers", {}),
                    "custom_args": email_data.get("custom_args", {}),
                }
                r = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    json=payload,
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                )
                return {"success": r.status_code in [200, 202], "error": None if r.status_code in [200, 202] else r.text}

            elif provider == "mailgun":
                domain = config.get("domain")
                data = {
                    "from": f"{email_data.get('from_name', '')} <{email_data.get('from_email', '')}>",
                    "to": email_data["to"],
                    "subject": email_data["subject"],
                    "html": email_data.get("html_body", ""),
                    "h:Reply-To": email_data.get("reply_to", ""),
                }
                for k, v in email_data.get("headers", {}).items():
                    data[f"h:{k}"] = v
                r = await client.post(
                    f"https://api.mailgun.net/v3/{domain}/messages",
                    auth=("api", api_key),
                    data=data
                )
                return {"success": r.status_code == 200, "error": None if r.status_code == 200 else r.text}

            elif provider == "postmark":
                payload = {
                    "From": f"{email_data.get('from_name', '')} <{email_data.get('from_email', '')}>",
                    "To": email_data["to"],
                    "Subject": email_data["subject"],
                    "HtmlBody": email_data.get("html_body", ""),
                    "TextBody": email_data.get("text_body", ""),
                    "Headers": [{"Name": k, "Value": v} for k, v in email_data.get("headers", {}).items()],
                    "Tag": email_data.get("tag", "hawkphish"),
                }
                r = await client.post(
                    "https://api.postmarkapp.com/email",
                    json=payload,
                    headers={"X-Postmark-Server-Token": api_key, "Accept": "application/json"}
                )
                return {"success": r.status_code == 200, "error": None}

            elif provider == "sparkpost":
                payload = {
                    "recipients": [{"address": {"email": email_data["to"]}}],
                    "content": {
                        "from": {"name": email_data.get("from_name", ""), "email": email_data.get("from_email", "")},
                        "subject": email_data["subject"],
                        "html": email_data.get("html_body", ""),
                    },
                    "headers": email_data.get("headers", {}),
                }
                r = await client.post(
                    "https://api.sparkpost.com/api/v1/transmissions",
                    json=payload,
                    headers={"Authorization": api_key, "Content-Type": "application/json"}
                )
                return {"success": r.status_code == 200, "error": None}

        return {"success": False, "error": "Unknown provider"}
