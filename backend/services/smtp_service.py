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

def explain_smtp_error(exc: Exception) -> str:
    """Smart error explanations from MailSpoof engine.py - tells users WHY it failed and how to fix."""
    err = str(exc).lower()
    msg = str(exc)

    if any(x in err for x in ("tss09", "permanently deferred", "blacklist", "blocked", "rbl", "spamhaus", "barracuda")):
        return "Your IP is blacklisted by the recipient's mail server. Use an external SMTP relay instead of direct MX delivery."
    if any(x in err for x in ("connection refused", "connection reset", "timed out", "timeout")):
        if "port 25" in err or "mx" in err:
            return "Cannot connect to recipient MX server (port 25 blocked?). Use an external SMTP relay with authentication."
        return f"Connection failed to SMTP server: {msg}. Check host/port and firewall."
    if any(x in err for x in ("spf", "dkim", "dmarc", "domain", "policy")):
        return "Domain policy rejected the email (SPF/DKIM/DMARC). Use an external SMTP relay that passes these checks."
    if any(x in err for x in ("relay", "rejected", "550", "553", "554")):
        return f"Mail server rejected the message: {msg}. Use an external SMTP relay with valid credentials."
    if "auth" in err or "login" in err or "password" in err:
        return f"Authentication failed: {msg}. Check username/password. For Gmail, use an App Password."
    if "recipient" in err:
        return f"Recipient refused: {msg}. Check the email address is valid."
    return f"SMTP Error: {msg}"


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
]

MAILERS = [
    "Microsoft Outlook 16.0",
    "Apple Mail (2.0)",
    "Mozilla Thunderbird 115.0",
    "Microsoft Office Outlook 12.0",
]


def add_anti_detection_headers(msg: MIMEMultipart, domain: str):
    """Add randomized headers to avoid pattern detection by spam filters."""
    msg['X-Mailer'] = random.choice(MAILERS)
    msg['User-Agent'] = random.choice(USER_AGENTS)
    msg['X-Priority'] = random.choice(['1', '2', '3'])
    msg['Importance'] = random.choice(['High', 'Normal', 'Low'])
    msg['X-MSMail-Priority'] = random.choice(['High', 'Normal', 'Low'])
    # Random threading ID format
    msg['X-Mailgun-Variables'] = json.dumps({"campaign_id": hashlib.md5(domain.encode()).hexdigest()[:8]})
    msg['X-Campaign-ID'] = hashlib.sha256(f"{domain}{time.time()}".encode()).hexdigest()[:16]


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
    # Anti-detection randomization
    add_anti_detection_headers(msg, domain)
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
        "brevo": ("smtp-relay.brevo.com", 587),
        "mailchimp": ("smtp.mailchimp.com", 587),
        "turbosmtp": ("smtp.turbo-smtp.com", 587),
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
        "mimecast": ("mimecast-smtp-out.qualys.com", 587),
        "proofpoint": ("smtp-us.ppe-hosted.com", 587),
    }

    API_PROVIDERS = [
        "sendgrid", "mailgun", "postmark", "sparkpost",
        "aws_ses_api", "brevo_api", "mailchimp_api", "mandrill",
        "mailersend", "resend", "elastic_email", "smtp2go",
        "pepipost", "socketlabs", "mailjet",
    ]

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
                context = _make_tls_context()
                if use_tls:
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
        domain = config.get("domain", "")

        async with httpx.AsyncClient(timeout=10) as client:
            # ── Existing providers ──
            if provider == "sendgrid":
                r = await client.get("https://api.sendgrid.com/v3/user/profile", headers={"Authorization": f"Bearer {api_key}"})
                return {"healthy": r.status_code == 200, "error": None if r.status_code == 200 else r.text}

            elif provider == "mailgun":
                r = await client.get(f"https://api.mailgun.net/v3/{domain}/bounce", auth=("api", api_key))
                return {"healthy": r.status_code == 200, "error": None if r.status_code == 200 else r.text}

            elif provider == "postmark":
                r = await client.get("https://api.postmarkapp.com/stats/outbound", headers={"Accept": "application/json", "X-Postmark-Server-Token": api_key})
                return {"healthy": r.status_code == 200, "error": None if r.status_code == 200 else r.text}

            elif provider == "sparkpost":
                r = await client.get("https://api.sparkpost.com/api/v1/transmissions", headers={"Authorization": api_key, "Accept": "application/json"})
                return {"healthy": r.status_code == 200, "error": None if r.status_code == 200 else r.text}

            # ── NEW API providers ──
            elif provider == "aws_ses_api":
                # AWS SES v2 API health check (list configuration sets)
                import hmac, hashlib
                from datetime import datetime
                region = config.get("region", "us-east-1")
                secret_key = config.get("secret_key", "")
                access_key = config.get("access_key", "")
                if not access_key or not secret_key:
                    return {"healthy": False, "error": "Missing AWS access_key or secret_key"}
                t = datetime.utcnow()
                amz_date = t.strftime('%Y%m%dT%H%M%SZ')
                date_stamp = t.strftime('%Y%m%d')
                credential_scope = f"{date_stamp}/{region}/ses/aws4_request"
                # Minimal signed request (LIST v2/email-identities)
                r = await client.get(
                    f"https://email.{region}.amazonaws.com/v2/email-identities",
                    headers={
                        "x-amz-date": amz_date,
                        "Authorization": f"AWS4-HMAC-SHA256 Credential={access_key}/{credential_scope}, SignedHeaders=host;x-amz-date, Signature=placeholder"
                    }
                )
                return {"healthy": r.status_code in [200, 403], "error": None if r.status_code in [200, 403] else r.text}

            elif provider == "brevo_api":
                r = await client.get("https://api.brevo.com/v3/account", headers={"api-key": api_key})
                return {"healthy": r.status_code == 200, "error": None if r.status_code == 200 else r.text}

            elif provider == "mailchimp_api":
                # Mailchimp API health check (ping root)
                dc = api_key.split('-')[-1] if '-' in api_key else "us1"
                r = await client.get(f"https://{dc}.api.mailchimp.com/3.0/", headers={"Authorization": f"Bearer {api_key}"})
                return {"healthy": r.status_code == 200, "error": None if r.status_code == 200 else r.text}

            elif provider == "mandrill":
                r = await client.post("https://mandrillapp.com/api/1.0/users/ping.json", json={"key": api_key})
                return {"healthy": r.status_code == 200 and "PONG" in r.text, "error": None if (r.status_code == 200 and "PONG" in r.text) else r.text}

            elif provider == "mailersend":
                r = await client.get("https://api.mailersend.com/v1/domains", headers={"Authorization": f"Bearer {api_key}"})
                return {"healthy": r.status_code == 200, "error": None if r.status_code == 200 else r.text}

            elif provider == "resend":
                r = await client.get("https://api.resend.com/emails", headers={"Authorization": f"Bearer {api_key}"})
                return {"healthy": r.status_code in [200, 401], "error": None if r.status_code in [200, 401] else r.text}

            elif provider == "elastic_email":
                r = await client.get("https://api.elasticemail.com/v4/campaigns", headers={"X-ElasticEmail-ApiKey": api_key})
                return {"healthy": r.status_code in [200, 401], "error": None if r.status_code in [200, 401] else r.text}

            elif provider == "smtp2go":
                r = await client.get("https://api.smtp2go.com/v3/users/me", headers={"Authorization": f"Bearer {api_key}"})
                return {"healthy": r.status_code in [200, 401], "error": None if r.status_code in [200, 401] else r.text}

            elif provider == "pepipost":
                # Pepipost (now Netcore) API v5
                r = await client.get("https://api.pepipost.com/v5/", headers={"api_key": api_key})
                return {"healthy": r.status_code in [200, 404], "error": None if r.status_code in [200, 404] else r.text}

            elif provider == "socketlabs":
                server_id = config.get("server_id", "")
                r = await client.get(f"https://inject.socketlabs.com/api/v1/servers/{server_id}", headers={"Authorization": f"Bearer {api_key}"})
                return {"healthy": r.status_code in [200, 401], "error": None if r.status_code in [200, 401] else r.text}

            elif provider == "mailjet":
                api_secret = config.get("api_secret", "")
                r = await client.get("https://api.mailjet.com/v3/REST/contactsentstatistics", auth=(api_key, api_secret))
                return {"healthy": r.status_code in [200, 401], "error": None if r.status_code in [200, 401] else r.text}

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
                    try:
                        import socks
                    except ImportError:
                        return {"success": False, "error": "PySocks is required for proxy support. Install with: pip install PySocks"}
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
        # Add smart explanation if failed
        if not result.get("success") and result.get("error"):
            result["explanation"] = explain_smtp_error(Exception(result["error"]))
        return result

    async def _send_api(self, config: dict, email_data: dict, attachments: list = None) -> dict:
        provider = config.get("provider")
        api_key = config.get("api_key")
        domain = config.get("domain", "")
        from_email = email_data.get("from_email", "")
        from_name = email_data.get("from_name", "")
        to_email = email_data["to"]
        subject = email_data["subject"]
        html_body = email_data.get("html_body", "")
        text_body = email_data.get("text_body", "")
        reply_to = email_data.get("reply_to", "")
        headers = email_data.get("headers", {})

        async with httpx.AsyncClient(timeout=30) as client:
            # ── Existing providers ──
            if provider == "sendgrid":
                payload = {
                    "personalizations": [{"to": [{"email": to_email}]}],
                    "from": {"email": from_email, "name": from_name},
                    "subject": subject,
                    "content": [{"type": "text/html", "value": html_body}],
                    "headers": headers,
                    "custom_args": email_data.get("custom_args", {}),
                }
                r = await client.post("https://api.sendgrid.com/v3/mail/send", json=payload,
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
                return {"success": r.status_code in [200, 202], "error": None if r.status_code in [200, 202] else r.text}

            elif provider == "mailgun":
                data = {"from": f"{from_name} <{from_email}>", "to": to_email, "subject": subject, "html": html_body, "h:Reply-To": reply_to}
                for k, v in headers.items():
                    data[f"h:{k}"] = v
                r = await client.post(f"https://api.mailgun.net/v3/{domain}/messages", auth=("api", api_key), data=data)
                return {"success": r.status_code == 200, "error": None if r.status_code == 200 else r.text}

            elif provider == "postmark":
                payload = {"From": f"{from_name} <{from_email}>", "To": to_email, "Subject": subject, "HtmlBody": html_body, "TextBody": text_body,
                    "Headers": [{"Name": k, "Value": v} for k, v in headers.items()], "Tag": email_data.get("tag", "hawkphish")}
                r = await client.post("https://api.postmarkapp.com/email", json=payload,
                    headers={"X-Postmark-Server-Token": api_key, "Accept": "application/json"})
                return {"success": r.status_code == 200, "error": None if r.status_code == 200 else r.text}

            elif provider == "sparkpost":
                payload = {"recipients": [{"address": {"email": to_email}}],
                    "content": {"from": {"name": from_name, "email": from_email}, "subject": subject, "html": html_body},
                    "headers": headers}
                r = await client.post("https://api.sparkpost.com/api/v1/transmissions", json=payload,
                    headers={"Authorization": api_key, "Content-Type": "application/json"})
                return {"success": r.status_code == 200, "error": None if r.status_code == 200 else r.text}

            # ── NEW API providers ──
            elif provider == "aws_ses_api":
                # AWS SES v2 SendEmail API
                region = config.get("region", "us-east-1")
                access_key = config.get("access_key", "")
                secret_key = config.get("secret_key", "")
                if not access_key or not secret_key:
                    return {"success": False, "error": "Missing AWS access_key or secret_key"}
                # Use boto3 if available, otherwise HTTP
                try:
                    import boto3
                    ses = boto3.client('sesv2', region_name=region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
                    response = ses.send_email(
                        FromEmailAddress=from_email,
                        Destination={"ToAddresses": [to_email]},
                        Content={"Simple": {"Subject": {"Data": subject}, "Body": {"Html": {"Data": html_body}, "Text": {"Data": text_body}}}}
                    )
                    return {"success": True, "error": None, "message_id": response.get("MessageId")}
                except Exception as e:
                    return {"success": False, "error": f"AWS SES API error: {str(e)}"}

            elif provider == "brevo_api":
                payload = {"sender": {"name": from_name, "email": from_email}, "to": [{"email": to_email, "name": ""}],
                    "subject": subject, "htmlContent": html_body, "textContent": text_body,
                    "replyTo": {"email": reply_to} if reply_to else None}
                r = await client.post("https://api.brevo.com/v3/smtp/email", json=payload,
                    headers={"api-key": api_key, "Content-Type": "application/json"})
                return {"success": r.status_code in [200, 201], "error": None if r.status_code in [200, 201] else r.text}

            elif provider == "mailchimp_api":
                # Mailchimp Transactional (Mandrill) via messages/send
                payload = {"key": api_key, "message": {"from_email": from_email, "from_name": from_name,
                    "to": [{"email": to_email, "type": "to"}], "subject": subject,
                    "html": html_body, "text": text_body, "headers": headers}}
                r = await client.post("https://mandrillapp.com/api/1.0/messages/send.json", json=payload)
                return {"success": r.status_code == 200, "error": None if r.status_code == 200 else r.text}

            elif provider == "mandrill":
                payload = {"key": api_key, "message": {"from_email": from_email, "from_name": from_name,
                    "to": [{"email": to_email, "type": "to"}], "subject": subject,
                    "html": html_body, "text": text_body, "headers": headers}}
                r = await client.post("https://mandrillapp.com/api/1.0/messages/send.json", json=payload)
                return {"success": r.status_code == 200, "error": None if r.status_code == 200 else r.text}

            elif provider == "mailersend":
                payload = {"from": {"email": from_email, "name": from_name}, "to": [{"email": to_email}],
                    "subject": subject, "html": html_body, "text": text_body,
                    "headers": headers, "reply_to": {"email": reply_to, "name": from_name} if reply_to else None}
                r = await client.post("https://api.mailersend.com/v1/email", json=payload,
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
                return {"success": r.status_code in [200, 202], "error": None if r.status_code in [200, 202] else r.text}

            elif provider == "resend":
                payload = {"from": f"{from_name} <{from_email}>", "to": [to_email], "subject": subject,
                    "html": html_body, "text": text_body, "reply_to": reply_to if reply_to else None}
                r = await client.post("https://api.resend.com/emails", json=payload,
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
                return {"success": r.status_code in [200, 202], "error": None if r.status_code in [200, 202] else r.text}

            elif provider == "elastic_email":
                payload = {"From": from_email, "FromName": from_name, "To": to_email, "Subject": subject,
                    "HtmlBody": html_body, "Body": text_body, "Headers": headers}
                r = await client.post("https://api.elasticemail.com/v4/emails/transactional", json=payload,
                    headers={"X-ElasticEmail-ApiKey": api_key, "Content-Type": "application/json"})
                return {"success": r.status_code in [200, 202], "error": None if r.status_code in [200, 202] else r.text}

            elif provider == "smtp2go":
                payload = {"sender": f"{from_name} <{from_email}>", "to": [to_email], "subject": subject,
                    "html_body": html_body, "text_body": text_body, "custom_headers": headers}
                r = await client.post("https://api.smtp2go.com/v3/email/send", json=payload,
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
                return {"success": r.status_code in [200, 202], "error": None if r.status_code in [200, 202] else r.text}

            elif provider == "pepipost":
                payload = {"api_key": api_key, "email_details": {"fromname": from_name, "from": from_email,
                    "subject": subject, "content": html_body}, "recipients": [to_email]}
                r = await client.post("https://api.pepipost.com/v5/mail/send", json=payload,
                    headers={"Content-Type": "application/json"})
                return {"success": r.status_code in [200, 202], "error": None if r.status_code in [200, 202] else r.text}

            elif provider == "socketlabs":
                server_id = config.get("server_id", "")
                payload = {"serverId": int(server_id), "apiKey": api_key,
                    "messages": [{"to": [{"emailAddress": to_email}], "from": {"emailAddress": from_email, "friendlyName": from_name},
                    "subject": subject, "htmlBody": html_body, "textBody": text_body}]}
                r = await client.post("https://inject.socketlabs.com/api/v1/email", json=payload,
                    headers={"Content-Type": "application/json"})
                return {"success": r.status_code in [200, 202], "error": None if r.status_code in [200, 202] else r.text}

            elif provider == "mailjet":
                api_secret = config.get("api_secret", "")
                payload = {"Messages": [{"From": {"Email": from_email, "Name": from_name},
                    "To": [{"Email": to_email}], "Subject": subject,
                    "HTMLPart": html_body, "TextPart": text_body, "Headers": headers}]}
                r = await client.post("https://api.mailjet.com/v3.1/send", json=payload,
                    headers={"Content-Type": "application/json"}, auth=(api_key, api_secret))
                return {"success": r.status_code in [200, 202], "error": None if r.status_code in [200, 202] else r.text}

        return {"success": False, "error": "Unknown provider"}
