"""HawkPhish - Advanced Tracking Service"""
import base64
import re
import httpx
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import EmailLog, Campaign, CredentialSubmit, RecipientSession

TRACKING_PIXEL = base64.b64decode(
    "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
)

BROWSER_PATTERNS = [
    (r"Edg(?:e|A|iOS)?/(\d+)", "Edge"),
    (r"Chrome/(\d+)", "Chrome"),
    (r"Firefox/(\d+)", "Firefox"),
    (r"Version/(\d+).*Safari/", "Safari"),
    (r"OPR/(\d+)", "Opera"),
    (r"SamsungBrowser/(\d+)", "Samsung Browser"),
    (r"UCBrowser/(\d+)", "UC Browser"),
    (r"Trident/7.*rv:(\d+)", "IE 11"),
    (r"Webkit/(\d+)", "WebKit"),
]

OS_PATTERNS = [
    (r"Windows NT 10\.0", "Windows 10/11"),
    (r"Windows NT 6\.3", "Windows 8.1"),
    (r"Windows NT 6\.2", "Windows 8"),
    (r"Windows NT 6\.1", "Windows 7"),
    (r"Windows", "Windows"),
    (r"Mac OS X (\d+[._]\d+)", "macOS"),
    (r"iPhone OS (\d+)", "iOS"),
    (r"iPad.*OS (\d+)", "iPadOS"),
    (r"Android (\d+)", "Android"),
    (r"Linux", "Linux"),
    (r"CrOS", "ChromeOS"),
    (r"Ubuntu", "Ubuntu"),
]

DEVICE_PATTERNS = [
    (r"Mobile|Android.*Mobile|iPhone|iPod", "Mobile"),
    (r"iPad|Tablet|Android(?!.*Mobile)", "Tablet"),
    (r"Windows|Mac|Linux|CrOS", "Desktop"),
]


def parse_user_agent(ua: str) -> dict:
    browser = "Unknown"
    browser_ver = ""
    for pattern, name in BROWSER_PATTERNS:
        m = re.search(pattern, ua)
        if m:
            browser = name
            browser_ver = m.group(1)
            break

    os_name = "Unknown"
    for pattern, name in OS_PATTERNS:
        if re.search(pattern, ua):
            os_name = name
            break

    device = "Unknown"
    for pattern, name in DEVICE_PATTERNS:
        if re.search(pattern, ua, re.IGNORECASE):
            device = name
            break

    return {
        "browser": f"{browser} {browser_ver}".strip() if browser_ver else browser,
        "os": os_name,
        "device": device,
    }


async def geoip_lookup(ip: str) -> dict:
    if not ip or ip in ("127.0.0.1", "::1", "localhost"):
        return {"country": "Local", "city": "", "region": "", "isp": "", "org": "", "timezone": ""}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,isp,org,timezone")
            if r.status_code == 200:
                data = r.json()
                if data.get("status") == "success":
                    return {
                        "country": data.get("country", ""),
                        "city": data.get("city", ""),
                        "region": data.get("regionName", ""),
                        "isp": data.get("isp", ""),
                        "org": data.get("org", ""),
                        "timezone": data.get("timezone", ""),
                    }
    except Exception:
        pass
    return {"country": "", "city": "", "region": "", "isp": "", "org": "", "timezone": ""}


def _make_event(event_type: str, data: dict) -> dict:
    return {"type": event_type, "time": datetime.utcnow().isoformat(), **data}


class TrackingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_or_create_session(self, campaign_id: int, recipient_id: int, email: str) -> RecipientSession:
        result = await self.db.execute(
            select(RecipientSession).where(
                RecipientSession.campaign_id == campaign_id,
                RecipientSession.recipient_id == recipient_id,
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            session = RecipientSession(
                campaign_id=campaign_id,
                recipient_id=recipient_id,
                email=email,
                events=[],
                ip_addresses=[],
                browsers=[],
                devices=[],
                countries=[],
            )
            self.db.add(session)
            await self.db.flush()
        return session

    def _add_event_to_session(self, session: RecipientSession, event: dict, ip: str = "", geo: dict = None, browser_info: dict = None):
        session.events.append(event)
        session.total_events = len(session.events)
        session.last_event_at = datetime.utcnow()
        if not session.first_event_at:
            session.first_event_at = datetime.utcnow()

        if ip and ip not in session.ip_addresses:
            session.ip_addresses.append(ip)
        if browser_info:
            b = browser_info.get("browser", "")
            if b and b not in session.browsers:
                session.browsers.append(b)
            d = browser_info.get("device", "")
            if d and d not in session.devices:
                session.devices.append(d)
        if geo:
            c = geo.get("country", "")
            if c and c not in session.countries:
                session.countries.append(c)

    async def record_open(self, tracking_id: str, user_agent: str = "", ip_address: str = "", language: str = "", referrer: str = ""):
        result = await self.db.execute(
            select(EmailLog).where(EmailLog.tracking_id == tracking_id)
        )
        log = result.scalar_one_or_none()
        if not log:
            return

        browser_info = parse_user_agent(user_agent)
        geo = await geoip_lookup(ip_address)

        log.open_count += 1
        if not log.opened_at:
            log.opened_at = datetime.utcnow()
            log.status = "opened"
            campaign = await self.db.get(Campaign, log.campaign_id)
            if campaign:
                campaign.total_opened += 1

        log.user_agent = user_agent
        log.ip_address = ip_address
        log.browser = browser_info["browser"]
        log.os = browser_info["os"]
        log.device = browser_info["device"]
        log.language = language
        log.referrer = referrer
        log.country = geo["country"]
        log.city = geo["city"]
        log.region = geo["region"]
        log.isp = geo["isp"]
        log.org = geo["org"]
        log.timezone = geo["timezone"]

        recipient = None
        if log.recipient_id:
            from models import Recipient
            recipient = await self.db.get(Recipient, log.recipient_id)

        session = await self._get_or_create_session(log.campaign_id, log.recipient_id or 0, recipient.email if recipient else "")
        event = _make_event("open", {
            "ip": ip_address, "browser": browser_info["browser"], "os": browser_info["os"],
            "device": browser_info["device"], "country": geo["country"], "city": geo["city"],
            "isp": geo["isp"], "language": language,
        })
        self._add_event_to_session(session, event, ip_address, geo, browser_info)
        session.status = "opened"

        await self.db.commit()

    async def record_click(self, tracking_id: str, user_agent: str = "", ip_address: str = "", language: str = "", referrer: str = "") -> str:
        result = await self.db.execute(
            select(EmailLog).where(EmailLog.tracking_id == tracking_id)
        )
        log = result.scalar_one_or_none()
        if not log:
            return "/"

        browser_info = parse_user_agent(user_agent)
        geo = await geoip_lookup(ip_address)

        log.click_count += 1
        if not log.clicked_at:
            log.clicked_at = datetime.utcnow()
            log.status = "clicked"
            campaign = await self.db.get(Campaign, log.campaign_id)
            if campaign:
                campaign.total_clicked += 1

        log.user_agent = user_agent
        log.ip_address = ip_address
        log.browser = browser_info["browser"]
        log.os = browser_info["os"]
        log.device = browser_info["device"]
        log.language = language
        log.referrer = referrer
        log.country = geo["country"]
        log.city = geo["city"]
        log.region = geo["region"]
        log.isp = geo["isp"]
        log.org = geo["org"]
        log.timezone = geo["timezone"]

        recipient = None
        if log.recipient_id:
            from models import Recipient
            recipient = await self.db.get(Recipient, log.recipient_id)

        session = await self._get_or_create_session(log.campaign_id, log.recipient_id or 0, recipient.email if recipient else "")
        event = _make_event("click", {
            "ip": ip_address, "browser": browser_info["browser"], "os": browser_info["os"],
            "device": browser_info["device"], "country": geo["country"], "city": geo["city"],
            "isp": geo["isp"], "language": language,
        })
        self._add_event_to_session(session, event, ip_address, geo, browser_info)
        session.status = "clicked"

        await self.db.commit()

        campaign = await self.db.get(Campaign, log.campaign_id)
        if campaign and campaign.landing_page_id:
            return f"/lp/{campaign.landing_page_id}"
        return "/"

    async def record_credential(self, tracking_id: str, email: str, password: str,
                                user_agent: str = "", ip_address: str = "", language: str = "", referrer: str = ""):
        result = await self.db.execute(
            select(EmailLog).where(EmailLog.tracking_id == tracking_id)
        )
        log = result.scalar_one_or_none()
        if not log:
            return

        browser_info = parse_user_agent(user_agent)
        geo = await geoip_lookup(ip_address)

        log.submitted_at = datetime.utcnow()
        log.status = "submitted"
        log.user_agent = user_agent
        log.ip_address = ip_address
        log.browser = browser_info["browser"]
        log.os = browser_info["os"]
        log.device = browser_info["device"]
        log.language = language
        log.country = geo["country"]
        log.city = geo["city"]
        log.isp = geo["isp"]

        submit = CredentialSubmit(
            campaign_id=log.campaign_id,
            recipient_id=log.recipient_id,
            email=email,
            password=password,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(submit)

        campaign = await self.db.get(Campaign, log.campaign_id)
        if campaign:
            campaign.total_submitted += 1

        recipient = None
        if log.recipient_id:
            from models import Recipient
            recipient = await self.db.get(Recipient, log.recipient_id)

        session = await self._get_or_create_session(log.campaign_id, log.recipient_id or 0, recipient.email if recipient else "")
        event = _make_event("submit", {
            "ip": ip_address, "email": email, "browser": browser_info["browser"], "os": browser_info["os"],
            "device": browser_info["device"], "country": geo["country"], "city": geo["city"],
            "isp": geo["isp"],
        })
        self._add_event_to_session(session, event, ip_address, geo, browser_info)
        session.status = "submitted"

        await self.db.commit()

    def get_pixel(self) -> bytes:
        return TRACKING_PIXEL
