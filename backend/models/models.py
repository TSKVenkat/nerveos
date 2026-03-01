"""SQLAlchemy models for NerveOS."""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime,
    ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship
import enum
from database import Base


# ── Enums ────────────────────────────────────────────────

class ActionStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"


class AlertSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class EmailPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class EmailCategory(str, enum.Enum):
    LEAD = "lead"
    RENEWAL_RISK = "renewal_risk"
    COMPLAINT = "complaint"
    PARTNERSHIP = "partnership"
    SPAM = "spam"
    GENERAL = "general"


# ── Competitors & Market Intel ───────────────────────────

class Competitor(Base):
    __tablename__ = "competitors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    domain = Column(String(255))
    description = Column(Text)
    keywords = Column(JSON, default=list)       # ["keyword1", "keyword2"]
    track_trends = Column(Boolean, default=True)
    track_news = Column(Boolean, default=True)
    track_finance = Column(Boolean, default=True)
    ticker_symbol = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    intel_reports = relationship("MarketIntelReport", back_populates="competitor")


class MarketIntelReport(Base):
    __tablename__ = "market_intel_reports"

    id = Column(Integer, primary_key=True, index=True)
    competitor_id = Column(Integer, ForeignKey("competitors.id"), nullable=True)
    report_type = Column(String(50))  # trends, news, finance, competitor_digest
    title = Column(String(500))
    summary = Column(Text)
    raw_data = Column(JSON)
    severity = Column(SAEnum(AlertSeverity), default=AlertSeverity.INFO)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    competitor = relationship("Competitor", back_populates="intel_reports")
    suggested_actions = relationship("SuggestedAction", back_populates="report")


# ── Email & CRM ──────────────────────────────────────────

class EmailAccount(Base):
    __tablename__ = "email_accounts"

    id = Column(Integer, primary_key=True, index=True)
    email_address = Column(String(255), nullable=False)
    display_name = Column(String(255))
    imap_host = Column(String(255))
    imap_port = Column(Integer, default=993)
    smtp_host = Column(String(255))
    smtp_port = Column(Integer, default=587)
    username = Column(String(255))
    password_encrypted = Column(String(500))
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    emails = relationship("EmailMessage", back_populates="account")


class EmailMessage(Base):
    __tablename__ = "email_messages"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("email_accounts.id"))
    message_id = Column(String(500))  # email Message-ID header
    from_address = Column(String(255))
    to_address = Column(String(255))
    subject = Column(String(500))
    body_text = Column(Text)
    body_html = Column(Text)
    received_at = Column(DateTime)
    is_read = Column(Boolean, default=False)
    category = Column(SAEnum(EmailCategory), default=EmailCategory.GENERAL)
    priority = Column(SAEnum(EmailPriority), default=EmailPriority.MEDIUM)
    ai_summary = Column(Text)
    sentiment_score = Column(Float)
    needs_reply = Column(Boolean, default=False)
    reply_drafted = Column(Boolean, default=False)
    follow_up_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    account = relationship("EmailAccount", back_populates="emails")
    draft_replies = relationship("DraftReply", back_populates="email")


class DraftReply(Base):
    __tablename__ = "draft_replies"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("email_messages.id"))
    tone = Column(String(50))  # professional, friendly, firm
    body = Column(Text)
    status = Column(SAEnum(ActionStatus), default=ActionStatus.PENDING)
    approved_by = Column(String(255), nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    email = relationship("EmailMessage", back_populates="draft_replies")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    email = Column(String(255))
    company = Column(String(255))
    role = Column(String(255))
    phone = Column(String(50))
    tags = Column(JSON, default=list)
    deal_value = Column(Float, default=0.0)
    deal_stage = Column(String(50), default="new")  # new, contacted, qualified, proposal, won, lost
    notes = Column(Text)
    last_contacted = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── Executive Dashboard / Metrics ────────────────────────

class BusinessMetric(Base):
    __tablename__ = "business_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100))  # mrr, arr, churn_rate, new_leads, nps, tickets_open
    metric_value = Column(Float)
    metric_unit = Column(String(50))
    period = Column(String(20))  # 2024-01, 2024-W05, 2024-01-15
    source = Column(String(100))  # manual, stripe, db_computed
    metadata_ = Column("metadata", JSON, default=dict)
    recorded_at = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500))
    message = Column(Text)
    severity = Column(SAEnum(AlertSeverity), default=AlertSeverity.INFO)
    source = Column(String(100))  # market_intel, email_agent, cockpit, system
    is_read = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)
    related_entity_type = Column(String(50))  # competitor, email, metric
    related_entity_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Actions & Guardrails ─────────────────────────────────

class SuggestedAction(Base):
    __tablename__ = "suggested_actions"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("market_intel_reports.id"), nullable=True)
    action_type = Column(String(100))  # send_email, update_deal, create_task, alert, campaign
    title = Column(String(500))
    description = Column(Text)
    parameters = Column(JSON, default=dict)
    status = Column(SAEnum(ActionStatus), default=ActionStatus.PENDING)
    requires_approval = Column(Boolean, default=True)
    approved_by = Column(String(255), nullable=True)
    executed_at = Column(DateTime, nullable=True)
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    report = relationship("MarketIntelReport", back_populates="suggested_actions")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(100))
    action = Column(String(200))
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    input_data = Column(JSON)
    output_data = Column(JSON)
    user_approved = Column(Boolean, default=False)
    approved_by = Column(String(255), nullable=True)
    status = Column(String(50))
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    description = Column(Text)
    rule_type = Column(String(50))  # block, require_approval, auto_approve
    conditions = Column(JSON)  # {"action_type": "send_email", "deal_value_gt": 10000}
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Watched Keywords / Topics ────────────────────────────

class WatchedTopic(Base):
    __tablename__ = "watched_topics"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String(255), nullable=False)
    topic_type = Column(String(50))  # keyword, industry, technology, ticker
    track_trends = Column(Boolean, default=True)
    track_news = Column(Boolean, default=True)
    track_finance = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
