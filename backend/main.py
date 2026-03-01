"""
NerveOS — AI-Native Business Operating System
Main FastAPI application.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from config import settings
from database import init_db, async_session
from routers import market, email, dashboard, actions
from routers import settings as settings_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown."""
    logger.info("🚀 NerveOS v{} starting...", settings.APP_VERSION)
    await init_db()
    await seed_demo_data()
    logger.info("✅ Database initialized")
    yield
    logger.info("👋 NerveOS shutting down")


app = FastAPI(
    title="NerveOS",
    description="AI-Native Business Operating System — Market Intel · Email Agent · Executive Cockpit",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS — allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(market.router)
app.include_router(email.router)
app.include_router(dashboard.router)
app.include_router(actions.router)
app.include_router(settings_router.router)


@app.get("/")
async def root():
    return {
        "app": "NerveOS",
        "version": settings.APP_VERSION,
        "tagline": "AI Business OS — continuously watches your market, inbox, and metrics.",
        "docs": "/docs",
        "dashboard": "/api/dashboard",
    }


@app.get("/api/status")
async def status():
    return {"status": "operational", "version": settings.APP_VERSION}


async def seed_demo_data():
    """Seed some demo data for hackathon demo."""
    from models.models import (
        Competitor, WatchedTopic, BusinessMetric, Contact,
        PolicyRule, Alert, AlertSeverity
    )
    from sqlalchemy import select

    async with async_session() as db:
        # Check if already seeded
        result = await db.execute(select(Competitor).limit(1))
        if result.scalar_one_or_none():
            return

        logger.info("🌱 Seeding demo data...")

        # Competitors
        competitors = [
            Competitor(
                name="Zoho", domain="zoho.com",
                description="Enterprise SaaS suite",
                keywords=["zoho crm", "zoho one", "zoho books"],
                ticker_symbol="", track_finance=False,
            ),
            Competitor(
                name="Freshworks", domain="freshworks.com",
                description="Customer engagement software",
                keywords=["freshdesk", "freshsales", "freshworks crm"],
                ticker_symbol="FRSH", track_finance=True,
            ),
            Competitor(
                name="HubSpot", domain="hubspot.com",
                description="Inbound marketing and CRM",
                keywords=["hubspot crm", "hubspot marketing", "inbound marketing"],
                ticker_symbol="HUBS", track_finance=True,
            ),
        ]
        db.add_all(competitors)

        # Watched topics
        topics = [
            WatchedTopic(topic="AI business automation", topic_type="technology"),
            WatchedTopic(topic="SaaS market India", topic_type="industry"),
            WatchedTopic(topic="no-code tools", topic_type="technology"),
            WatchedTopic(topic="enterprise AI agents", topic_type="technology"),
        ]
        db.add_all(topics)

        # Business metrics (last 6 months)
        import random
        from datetime import datetime, timedelta
        base_mrr = 50000
        for i in range(6):
            month = (datetime.utcnow() - timedelta(days=30 * (5 - i))).strftime("%Y-%m")
            mrr = base_mrr + random.randint(-2000, 5000) * (i + 1)
            db.add(BusinessMetric(metric_name="mrr", metric_value=mrr, metric_unit="USD", period=month, source="seed"))
            db.add(BusinessMetric(metric_name="new_leads", metric_value=random.randint(20, 80), metric_unit="count", period=month, source="seed"))
            db.add(BusinessMetric(metric_name="churn_rate", metric_value=round(random.uniform(1.5, 5.0), 1), metric_unit="%", period=month, source="seed"))
            db.add(BusinessMetric(metric_name="nps_score", metric_value=random.randint(30, 70), metric_unit="score", period=month, source="seed"))
            db.add(BusinessMetric(metric_name="support_tickets", metric_value=random.randint(10, 50), metric_unit="count", period=month, source="seed"))

        # Contacts
        contacts = [
            Contact(name="Raj Mehta", email="raj@acmecorp.in", company="Acme Corp", role="CTO",
                    deal_value=25000, deal_stage="proposal", tags=["enterprise", "hot"]),
            Contact(name="Priya Sharma", email="priya@techstart.io", company="TechStart", role="CEO",
                    deal_value=8000, deal_stage="qualified", tags=["startup", "saas"]),
            Contact(name="Ankit Patel", email="ankit@bigretail.com", company="BigRetail", role="VP Engineering",
                    deal_value=50000, deal_stage="contacted", tags=["enterprise", "retail"]),
            Contact(name="Sarah Chen", email="sarah@globalfin.com", company="GlobalFin", role="COO",
                    deal_value=15000, deal_stage="new", tags=["fintech"]),
            Contact(name="Vikram Singh", email="vikram@cloudnine.dev", company="CloudNine", role="Founder",
                    deal_value=5000, deal_stage="won", tags=["startup"]),
        ]
        db.add_all(contacts)

        # Default policy rules
        policies = [
            PolicyRule(
                name="Email approval required",
                description="All outgoing emails require human approval before sending",
                rule_type="require_approval",
                conditions={"action_type": "send_email"},
                priority=10,
            ),
            PolicyRule(
                name="High-value deal protection",
                description="Changes to deals above $20,000 require manager approval",
                rule_type="require_approval",
                conditions={"action_type": "update_deal", "deal_value_gt": 20000},
                priority=20,
            ),
        ]
        db.add_all(policies)

        # Sample alerts
        alerts = [
            Alert(
                title="Freshworks Q4 earnings beat expectations",
                message="FRSH reported 22% YoY revenue growth. Consider reviewing competitive positioning.",
                severity=AlertSeverity.WARNING, source="market_intel",
            ),
            Alert(
                title="New lead spike: 15 signups this week",
                message="Unusual increase in signups — 3x weekly average. Investigate source.",
                severity=AlertSeverity.INFO, source="executive_cockpit",
            ),
        ]
        db.add_all(alerts)

        await db.commit()
        logger.info("✅ Demo data seeded")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
