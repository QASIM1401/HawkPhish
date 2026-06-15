"""HawkPhish - Campaign Manager"""
import asyncio
import uuid
import random
import string
import re
import html as html_module
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from models import Campaign, EmailLog, Recipient, SMTPConfig, EmailTemplate, LandingPage, CredentialSubmit, Group, ProxyConfig
from services.smtp_service import SMTPSender, validate_email
from services.template_engine import TemplateEngine
import hashlib


class CampaignManager:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.smtp_sender = SMTPSender()
        self.template_engine = TemplateEngine()
        self._running_campaigns = {}

    async def create_campaign(self, data: dict) -> Campaign:
        campaign = Campaign(
            name=data["name"],
            template_id=data["template_id"],
            landing_page_id=data.get("landing_page_id"),
            smtp_id=data["smtp_id"],
            group_id=data["group_id"],
            use_proxies=data.get("use_proxies", False),
            settings=data.get("settings", {}),
            subject_rotation=data.get("subject_rotation", 1),
            fromname_rotation=data.get("fromname_rotation", 1),
            letter_rotation=data.get("letter_rotation", False),
            reply_to=data.get("reply_to"),
            bcc=data.get("bcc"),
            cc=data.get("cc"),
            spoof_from=data.get("spoof_from"),
            attachments=data.get("attachments", []),
            disclaimer_enabled=data.get("disclaimer_enabled", False),
            custom_headers=data.get("custom_headers", {}),
        )
        self.db.add(campaign)
        await self.db.commit()
        await self.db.refresh(campaign)
        return campaign

    async def start_campaign(self, campaign_id: int):
        campaign = await self.db.get(Campaign, campaign_id)
        if not campaign or campaign.status not in ["draft", "paused"]:
            return {"error": "Campaign cannot be started"}

        campaign.status = "running"
        campaign.started_at = datetime.utcnow()
        await self.db.commit()

        asyncio.create_task(self._process_campaign(campaign_id))
        return {"message": "Campaign started"}

    async def pause_campaign(self, campaign_id: int):
        campaign = await self.db.get(Campaign, campaign_id)
        if not campaign or campaign.status != "running":
            return {"error": "Campaign is not running"}
        campaign.status = "paused"
        await self.db.commit()
        self._running_campaigns.pop(campaign_id, None)
        return {"message": "Campaign paused"}

    async def cancel_campaign(self, campaign_id: int):
        campaign = await self.db.get(Campaign, campaign_id)
        if not campaign:
            return {"error": "Campaign not found"}
        campaign.status = "cancelled"
        await self.db.commit()
        self._running_campaigns.pop(campaign_id, None)
        return {"message": "Campaign cancelled"}

    async def _process_campaign(self, campaign_id: int):
        self._running_campaigns[campaign_id] = True

        campaign = await self.db.get(Campaign, campaign_id)
        template = await self.db.get(EmailTemplate, campaign.template_id)
        smtp = await self.db.get(SMTPConfig, campaign.smtp_id)
        group = await self.db.get(Group, campaign.group_id)
        landing_page = await self.db.get(LandingPage, campaign.landing_page_id) if campaign.landing_page_id else None

        proxies = []
        if campaign.use_proxies:
            result_p = await self.db.execute(
                select(ProxyConfig).where(ProxyConfig.is_active == True, ProxyConfig.is_healthy == True)
            )
            proxies = result_p.scalars().all()

        result = await self.db.execute(
            select(Recipient).where(Recipient.group_id == group.id)
        )
        recipients = result.scalars().all()

        settings = campaign.settings or {}
        min_delay = settings.get("min_delay", 2)
        max_delay = settings.get("max_delay", 8)
        max_per_smtp = smtp.max_emails - smtp.emails_sent

        # Load rotation data
        subjects = [s.strip() for s in template.subject.split(";") if s.strip()] if ";" in template.subject else [template.subject]
        from_names = [n.strip() for n in (smtp.from_name or "").split(";") if n.strip()] if ";" in (smtp.from_name or "") else [smtp.from_name or ""]
        
        # Letter rotation: support multiple templates if configured
        templates = [template]
        if campaign.letter_rotation:
            extra_tpl_ids = settings.get("extra_template_ids", [])
            if extra_tpl_ids:
                for tid in extra_tpl_ids:
                    t = await self.db.get(EmailTemplate, tid)
                    if t:
                        templates.append(t)

        proxy_index = campaign.proxy_index or 0
        sent_count = 0
        for i, recipient in enumerate(recipients):
            if campaign_id not in self._running_campaigns:
                break
            if sent_count >= max_per_smtp:
                break

            # Validate recipient email
            if not validate_email(recipient.email):
                log = EmailLog(
                    campaign_id=campaign_id,
                    recipient_id=recipient.id,
                    smtp_id=smtp.id,
                    tracking_id="invalid",
                    status="failed",
                    error_message=f"Invalid email: {recipient.email}",
                )
                self.db.add(log)
                campaign.total_failed += 1
                await self.db.commit()
                continue

            tracking_id = str(uuid.uuid4())[:16]
            landing_url = ""
            if landing_page:
                landing_url = f"{settings.get('base_url', 'http://localhost:8000')}/lp/{landing_page.id}"

            variables = {
                "email": recipient.email,
                "first_name": recipient.first_name or "",
                "last_name": recipient.last_name or "",
                "position": recipient.position or "",
                "domain": recipient.email.split("@")[1] if "@" in recipient.email else "",
                "date": datetime.utcnow().strftime("%B %d, %Y"),
                "tracking_id": tracking_id,
                "link": f"{settings.get('base_url', 'http://localhost:8000')}/track/{tracking_id}",
            }

            # Rotation logic
            subject_idx = (i // campaign.subject_rotation) % len(subjects) if campaign.subject_rotation > 0 else 0
            fromname_idx = (i // campaign.fromname_rotation) % len(from_names) if campaign.fromname_rotation > 0 else 0
            tpl_idx = i % len(templates) if campaign.letter_rotation else 0
            
            current_template = templates[tpl_idx]
            current_subject = subjects[subject_idx]
            current_from_name = from_names[fromname_idx]

            rendered = self.template_engine.render(
                current_subject,
                current_template.html_body,
                current_template.text_body or "",
                variables,
                disclaimer=campaign.disclaimer_enabled,
                scenario_name=current_template.name,
                severity=current_template.severity or "Medium",
            )

            # Replace inline variables in HTML body (sender.py pattern)
            html_body = rendered["html_body"]
            html_body = html_body.replace("##email##", recipient.email)
            html_body = html_body.replace("##link##", f"{settings.get('base_url', 'http://localhost:8000')}/track/{tracking_id}")
            html_body = html_body.replace("##date##", datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))

            open_pixel = f'<img src="{settings.get("base_url", "http://localhost:8000")}/pixel/{tracking_id}" width="1" height="1" style="display:none" />'
            html_body = html_body + open_pixel

            # Build custom headers
            headers = {
                "X-Campaign-ID": str(campaign_id),
                "X-Tracking-ID": tracking_id,
                "X-Mailer": "HawkPhish",
                "X-Priority": "3",
                "X-MSMail-Priority": "Normal",
                "Importance": "Normal",
                "Precedence": "bulk",
                "X-Email-Type": "Promotional",
                "X-Job-ID": str(uuid.uuid4()),
            }
            if campaign.custom_headers:
                headers.update(campaign.custom_headers)

            email_data = {
                "to": recipient.email,
                "from_email": campaign.spoof_from or smtp.from_email,
                "from_name": current_from_name,
                "subject": rendered["subject"],
                "html_body": html_body,
                "text_body": rendered["text_body"],
                "message_id": f"<{tracking_id}@hawkphish>",
                "headers": headers,
                "reply_to": campaign.reply_to,
                "bcc": campaign.bcc,
                "cc": campaign.cc,
                "spoof_from": campaign.spoof_from,
                "domain": smtp.from_email.split("@")[1] if "@" in smtp.from_email else "localhost",
                "real_username": smtp.username or smtp.from_email,
            }

            log = EmailLog(
                campaign_id=campaign_id,
                recipient_id=recipient.id,
                smtp_id=smtp.id,
                tracking_id=tracking_id,
                status="sending",
            )
            self.db.add(log)
            await self.db.commit()

            proxy_dict = None
            if proxies:
                p = proxies[proxy_index % len(proxies)]
                proxy_dict = {
                    "proxy_type": p.proxy_type, "host": p.host, "port": p.port,
                    "username": p.username, "password": p.password,
                }
                p.total_uses += 1
                proxy_index += 1

            result = await self.smtp_sender.send(
                {
                    "provider": smtp.provider,
                    "host": smtp.host,
                    "port": smtp.port,
                    "username": smtp.username,
                    "password": smtp.password,
                    "api_key": smtp.api_key,
                    "use_tls": smtp.use_tls,
                    "domain": smtp.from_email.split("@")[1] if "@" in smtp.from_email else "",
                },
                email_data,
                proxy=proxy_dict,
                attachments=campaign.attachments,
            )

            if result["success"]:
                log.status = "sent"
                log.sent_at = datetime.utcnow()
                campaign.total_sent += 1
                smtp.emails_sent += 1
            else:
                log.status = "failed"
                log.error_message = result.get("error", "Unknown error")
                campaign.total_failed += 1

            await self.db.commit()
            sent_count += 1

            await asyncio.sleep(random.uniform(min_delay, max_delay))

        campaign.proxy_index = proxy_index
        campaign.status = "completed"
        campaign.completed_at = datetime.utcnow()
        await self.db.commit()
        self._running_campaigns.pop(campaign_id, None)

    async def get_stats(self, campaign_id: int) -> dict:
        campaign = await self.db.get(Campaign, campaign_id)
        if not campaign:
            return {}

        total = campaign.total_sent
        opened = campaign.total_opened
        clicked = campaign.total_clicked
        submitted = campaign.total_submitted

        return {
            "campaign_id": campaign_id,
            "name": campaign.name,
            "status": campaign.status,
            "total_sent": total,
            "total_opened": opened,
            "total_clicked": clicked,
            "total_submitted": submitted,
            "total_bounced": campaign.total_bounced,
            "total_failed": campaign.total_failed,
            "open_rate": round((opened / total * 100) if total > 0 else 0, 1),
            "click_rate": round((clicked / total * 100) if total > 0 else 0, 1),
            "submit_rate": round((submitted / total * 100) if total > 0 else 0, 1),
            "bounce_rate": round((campaign.total_bounced / total * 100) if total > 0 else 0, 1),
        }

    async def get_timeline(self, campaign_id: int) -> list:
        result = await self.db.execute(
            select(EmailLog)
            .where(EmailLog.campaign_id == campaign_id)
            .order_by(EmailLog.sent_at.desc())
        )
        logs = result.scalars().all()

        timeline = []
        for log in logs:
            recipient = await self.db.get(Recipient, log.recipient_id)
            events = []
            if log.sent_at:
                events.append({"event": "sent", "time": log.sent_at.isoformat()})
            if log.opened_at:
                events.append({"event": "opened", "time": log.opened_at.isoformat()})
            if log.clicked_at:
                events.append({"event": "clicked", "time": log.clicked_at.isoformat()})
            if log.submitted_at:
                events.append({"event": "submitted", "time": log.submitted_at.isoformat()})

            timeline.append({
                "email": recipient.email if recipient else "unknown",
                "name": f"{recipient.first_name} {recipient.last_name}" if recipient else "",
                "tracking_id": log.tracking_id,
                "status": log.status,
                "events": events,
            })

        return timeline
