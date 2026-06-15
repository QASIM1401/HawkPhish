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
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import httpx
import hashlib

logger = logging.getLogger("hawkphish.smtp")


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

        # Build proper MIME structure
        has_attachments = attachments and len(attachments) > 0
        if has_attachments:
            msg = MIMEMultipart("mixed")
            alt_part = MIMEMultipart("alternative")
        else:
            msg = MIMEMultipart("alternative")
            alt_part = msg

        msg["From"] = f"{email_data.get('from_name', '')} <{email_data.get('from_email', '')}>"
        msg["To"] = email_data["to"]
        msg["Subject"] = email_data["subject"]
        msg["Message-ID"] = email_data.get("message_id", f"<{hashlib.md5(str(time.time()).encode()).hexdigest()}@hawkphish>")
        msg["X-Mailer"] = email_data.get("x_mailer", "HawkPhish")
        msg["Date"] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')

        # Reply-To, BCC, CC
        if email_data.get("reply_to"):
            msg["Reply-To"] = email_data["reply_to"]
        if email_data.get("cc"):
            msg["Cc"] = email_data["cc"]
        if email_data.get("bcc"):
            msg["Bcc"] = email_data["bcc"]

        # Custom headers
        for key, value in email_data.get("headers", {}).items():
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
                    if not filepath or not os.path.isfile(filepath):
                        continue
                    with open(filepath, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                    encoders.encode_base64(part)
                    filename = os.path.basename(filepath)
                    part.add_header("Content-Disposition", f"attachment; filename={filename}")
                    msg.attach(part)
                except Exception as exc:
                    logger.warning(f"Failed to attach {att}: {exc}")

        loop = asyncio.get_event_loop()
        def _send():
            try:
                context = _make_tls_context()
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
