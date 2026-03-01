"""Agent Orchestrator — coordinates all agents and scheduled tasks."""

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from agents.market_intel import market_intel_agent
from agents.email_agent import email_agent
from agents.executive_cockpit import cockpit_agent
from guardrails.policy_engine import policy_engine


class Orchestrator:
    """
    Central orchestrator that:
    - Runs periodic agent tasks
    - Coordinates multi-agent workflows
    - Handles the approval queue
    """

    async def morning_briefing(self, db: AsyncSession) -> dict:
        """Generate a complete morning briefing for the business owner."""
        logger.info("🌅 Orchestrator: Generating morning briefing...")

        results = {}

        # 1. Market Intel scan
        try:
            intel = await market_intel_agent.run_full_scan(db)
            results["market_intel"] = {"status": "ok", "reports": len(intel)}
        except Exception as e:
            logger.error("Market intel error: {}", e)
            results["market_intel"] = {"status": "error", "message": str(e)}

        # 2. Email sync & triage
        try:
            email_sync = await email_agent.sync_inbox(db)
            inbox = await email_agent.get_inbox_summary(db)
            follow_ups = await email_agent.check_follow_ups(db)
            results["email"] = {
                "status": "ok",
                "new_emails": email_sync.get("new", 0),
                "inbox_summary": inbox,
                "follow_ups_needed": len(follow_ups),
            }
        except Exception as e:
            logger.error("Email agent error: {}", e)
            results["email"] = {"status": "error", "message": str(e)}

        # 3. Executive dashboard
        try:
            dashboard = await cockpit_agent.get_dashboard(db)
            anomalies = await cockpit_agent.check_metric_anomalies(db)
            results["dashboard"] = {
                "status": "ok",
                "data": dashboard,
                "anomalies": anomalies,
            }
        except Exception as e:
            logger.error("Cockpit error: {}", e)
            results["dashboard"] = {"status": "error", "message": str(e)}

        # 4. Pending actions
        try:
            pending = await policy_engine.get_pending_actions(db)
            results["pending_actions"] = len(pending)
        except Exception as e:
            results["pending_actions"] = 0

        results["generated_at"] = datetime.utcnow().isoformat()
        logger.info("✅ Orchestrator: Morning briefing complete")
        return results

    async def run_market_scan(self, db: AsyncSession) -> dict:
        """Run only market intelligence scan."""
        reports = await market_intel_agent.run_full_scan(db)
        return {"reports": len(reports), "details": reports}

    async def run_email_sync(self, db: AsyncSession) -> dict:
        """Run only email sync."""
        sync = await email_agent.sync_inbox(db)
        summary = await email_agent.get_inbox_summary(db)
        return {"sync": sync, "summary": summary}

    async def run_health_check(self, db: AsyncSession) -> dict:
        """Run only metrics health check."""
        anomalies = await cockpit_agent.check_metric_anomalies(db)
        return {"anomalies": anomalies}

    async def ask(self, db: AsyncSession, question: str) -> str:
        """Natural language interface to the business OS."""
        return await cockpit_agent.natural_language_query(db, question)


orchestrator = Orchestrator()
