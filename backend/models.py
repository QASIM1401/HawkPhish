"""HawkPhish - Database Models"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SMTPProvider(str, enum.Enum):
    CUSTOM = "custom"
    SENDGRID = "sendgrid"
    AWS_SES = "aws_ses"
    MAILGUN = "mailgun"
    POSTMARK = "postmark"
    SPARKPOST = "sparkpost"
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    OFFICE365 = "office365"
    MAILCHIMP = "mailchimp"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="admin")
    created_at = Column(DateTime, default=datetime.utcnow)


class SMTPConfig(Base):
    __tablename__ = "smtp_configs"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    provider = Column(String(20), default="custom")
    host = Column(String(255))
    port = Column(Integer, default=587)
    username = Column(String(255))
    password = Column(String(255))
    api_key = Column(String(500))
    from_email = Column(String(255))
    from_name = Column(String(100))
    use_tls = Column(Boolean, default=True)
    max_emails = Column(Integer, default=500)
    emails_sent = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_healthy = Column(Boolean, default=True)
    last_health_check = Column(DateTime)
    rate_limit = Column(Integer, default=50)
    retry_count = Column(Integer, default=3)
    profile_group = Column(String(50), default="default")  # Named profile groups
    created_at = Column(DateTime, default=datetime.utcnow)


class ProxyConfig(Base):
    __tablename__ = "proxy_configs"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    proxy_type = Column(String(20), default="http")
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(255))
    password = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_healthy = Column(Boolean, default=True)
    last_health_check = Column(DateTime)
    total_uses = Column(Integer, default=0)
    total_failures = Column(Integer, default=0)
    avg_latency = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    color = Column(String(7), default="#3B82F6")
    created_at = Column(DateTime, default=datetime.utcnow)
    recipients = relationship("Recipient", back_populates="group")


class Recipient(Base):
    __tablename__ = "recipients"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    position = Column(String(100))
    group_id = Column(Integer, ForeignKey("groups.id"))
    custom_data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    group = relationship("Group", back_populates="recipients")


class EmailTemplate(Base):
    __tablename__ = "email_templates"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    subject = Column(String(500), nullable=False)
    html_body = Column(Text, nullable=False)
    text_body = Column(Text)
    category = Column(String(50), default="general")
    severity = Column(String(20), default="Medium")  # Critical, High, Medium, Low
    tags = Column(JSON, default=list)
    variables = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LandingPage(Base):
    __tablename__ = "landing_pages"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    url = Column(String(500))
    html_content = Column(Text)
    capture_credentials = Column(Boolean, default=True)
    capture_fields = Column(JSON, default=list)
    redirect_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)


class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    status = Column(String(20), default="draft")
    template_id = Column(Integer, ForeignKey("email_templates.id"))
    landing_page_id = Column(Integer, ForeignKey("landing_pages.id"))
    smtp_id = Column(Integer, ForeignKey("smtp_configs.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    use_proxies = Column(Boolean, default=False)
    proxy_index = Column(Integer, default=0)
    scheduled_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    total_sent = Column(Integer, default=0)
    total_opened = Column(Integer, default=0)
    total_clicked = Column(Integer, default=0)
    total_submitted = Column(Integer, default=0)
    total_bounced = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)
    settings = Column(JSON, default={})
    # Rotation & advanced settings
    subject_rotation = Column(Integer, default=1)
    fromname_rotation = Column(Integer, default=1)
    letter_rotation = Column(Boolean, default=False)
    reply_to = Column(String(255))
    bcc = Column(String(500))
    cc = Column(String(500))
    attachments = Column(JSON, default=list)
    disclaimer_enabled = Column(Boolean, default=False)
    custom_headers = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)


class EmailLog(Base):
    __tablename__ = "email_logs"
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    recipient_id = Column(Integer, ForeignKey("recipients.id"))
    smtp_id = Column(Integer, ForeignKey("smtp_configs.id"))
    tracking_id = Column(String(50), unique=True, nullable=False)
    status = Column(String(20), default="queued")
    sent_at = Column(DateTime)
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    submitted_at = Column(DateTime)
    bounced_at = Column(DateTime)
    error_message = Column(Text)
    user_agent = Column(Text)
    ip_address = Column(String(45))
    browser = Column(String(50))
    os = Column(String(50))
    device = Column(String(50))
    country = Column(String(100))
    city = Column(String(100))
    region = Column(String(100))
    isp = Column(String(200))
    org = Column(String(200))
    timezone = Column(String(50))
    referrer = Column(Text)
    language = Column(String(50))
    open_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)


class RecipientSession(Base):
    __tablename__ = "recipient_sessions"
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    recipient_id = Column(Integer, ForeignKey("recipients.id"))
    email = Column(String(255))
    events = Column(JSON, default=list)
    first_event_at = Column(DateTime)
    last_event_at = Column(DateTime)
    total_events = Column(Integer, default=0)
    status = Column(String(20), default="sent")
    ip_addresses = Column(JSON, default=list)
    browsers = Column(JSON, default=list)
    devices = Column(JSON, default=list)
    countries = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CredentialSubmit(Base):
    __tablename__ = "credential_submits"
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    recipient_id = Column(Integer, ForeignKey("recipients.id"))
    email = Column(String(255))
    password = Column(String(255))
    submitted_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))
    user_agent = Column(Text)
