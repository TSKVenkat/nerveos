"""Executive Cockpit Agent — business health monitoring and NL queries."""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from loguru import logger

from models.models import (
    BusinessMetric, Alert, AlertSeverity,
    Contact, EmailMessage, MarketIntelReport
)
from services.llm import llm_service


class ExecutiveCockpitAgent:
    """
    Business health dashboard agent.

    Capabilities:
    - Unified KPI dashboard (MRR, churn, leads, NPS)
    - Week-over-week / month-over-month alerts
    - Natural language business queries
    - Anomaly detection in metrics
    """

    AGENT_NAME = "executive_cockpit"

    async def get_dashboard(self, db: AsyncSession) -> dict:
        """Get the full executive dashboard data."""
        logger.info("📊 Executive Cockpit: Building dashboard...")

        metrics = await self._get_latest_metrics(db)
        pipeline = await self._get_pipeline_summary(db)
        recent_alerts = await self._get_recent_alerts(db)
        intel_summary = await self._get_intel_summary(db)

        return {
            "metrics": metrics,
            "pipeline": pipeline,
            "alerts": recent_alerts,
            "intel_summary": intel_summary,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def _get_latest_metrics(self, db: AsyncSession) -> dict:
        """Get latest value for each tracked metric."""
        # Get distinct metric names
        result = await db.execute(
            select(BusinessMetric.metric_name).distinct()
        )
        metric_names = [row[0] for row in result.all()]

        latest = {}
        for name in metric_names:
            result = await db.execute(
                select(BusinessMetric)
                .where(BusinessMetric.metric_name == name)
                .order_by(desc(BusinessMetric.recorded_at))
                .limit(2)
            )
            records = result.scalars().all()
            if records:
                current = records[0]
                previous = records[1] if len(records) > 1 else None
                change = None
                if previous and previous.metric_value and previous.metric_value != 0:
                    change = round(
                        ((current.metric_value - previous.metric_value) / previous.metric_value) * 100, 1
                    )
                latest[name] = {
                    "value": current.metric_value,
                    "unit": current.metric_unit,
                    "period": current.period,
                    "change_pct": change,
                    "recorded_at": current.recorded_at.isoformat(),
                }

        return latest

    async def _get_pipeline_summary(self, db: AsyncSession) -> dict:
        """Summarize the sales pipeline from contacts."""
        result = await db.execute(select(Contact))
        contacts = result.scalars().all()

        stages = {}
        total_value = 0
        for c in contacts:
            stage = c.deal_stage or "new"
            if stage not in stages:
                stages[stage] = {"count": 0, "value": 0}
            stages[stage]["count"] += 1
            stages[stage]["value"] += c.deal_value or 0
            total_value += c.deal_value or 0

        return {
            "total_contacts": len(contacts),
            "total_pipeline_value": total_value,
            "by_stage": stages,
        }

    async def _get_recent_alerts(self, db: AsyncSession, limit: int = 10) -> list[dict]:
        result = await db.execute(
            select(Alert)
            .where(Alert.is_dismissed == False)
            .order_by(desc(Alert.created_at))
            .limit(limit)
        )
        alerts = result.scalars().all()
        return [
            {
                "id": a.id,
                "title": a.title,
                "message": a.message,
                "severity": a.severity.value if a.severity else "info",
                "source": a.source,
                "is_read": a.is_read,
                "created_at": a.created_at.isoformat(),
            }
            for a in alerts
        ]

    async def _get_intel_summary(self, db: AsyncSession) -> dict:
        """Count recent intel reports."""
        week_ago = datetime.utcnow() - timedelta(days=7)
        result = await db.execute(
            select(func.count(MarketIntelReport.id))
            .where(MarketIntelReport.created_at >= week_ago)
        )
        report_count = result.scalar() or 0

        result = await db.execute(
            select(func.count(MarketIntelReport.id))
            .where(
                and_(
                    MarketIntelReport.created_at >= week_ago,
                    MarketIntelReport.is_read == False,
                )
            )
        )
        unread_count = result.scalar() or 0

        return {
            "reports_this_week": report_count,
            "unread_reports": unread_count,
        }

    async def check_metric_anomalies(self, db: AsyncSession) -> list[dict]:
        """Detect anomalies in business metrics and create alerts."""
        result = await db.execute(
            select(BusinessMetric.metric_name).distinct()
        )
        metric_names = [row[0] for row in result.all()]

        anomalies = []
        for name in metric_names:
            result = await db.execute(
                select(BusinessMetric)
                .where(BusinessMetric.metric_name == name)
                .order_by(desc(BusinessMetric.recorded_at))
                .limit(5)
            )
            records = result.scalars().all()
            if len(records) < 3:
                continue

            current = records[0].metric_value
            historical_avg = sum(r.metric_value for r in records[1:]) / len(records[1:])

            if historical_avg == 0:
                continue

            pct_change = ((current - historical_avg) / historical_avg) * 100

            if abs(pct_change) > 15:  # 15% threshold
                direction = "increased" if pct_change > 0 else "decreased"
                severity = AlertSeverity.CRITICAL if abs(pct_change) > 30 else AlertSeverity.WARNING

                alert = Alert(
                    title=f"{name} {direction} by {abs(pct_change):.1f}%",
                    message=f"Current: {current} | Avg (last {len(records)-1} periods): {historical_avg:.1f}",
                    severity=severity,
                    source=self.AGENT_NAME,
                    related_entity_type="metric",
                )
                db.add(alert)
                anomalies.append({
                    "metric": name,
                    "current": current,
                    "average": round(historical_avg, 1),
                    "change_pct": round(pct_change, 1),
                    "severity": severity.value,
                })

        await db.commit()
        return anomalies

    async def natural_language_query(self, db: AsyncSession, question: str) -> str:
        """Answer a business question in natural language."""
        # Gather context
        metrics = await self._get_latest_metrics(db)
        pipeline = await self._get_pipeline_summary(db)

        context = f"""Business Metrics:
{self._format_metrics(metrics)}

Sales Pipeline:
Total contacts: {pipeline['total_contacts']}
Total pipeline value: {pipeline['total_pipeline_value']}
By stage: {pipeline['by_stage']}
"""
        return await llm_service.natural_language_query(question, context)

    def _format_metrics(self, metrics: dict) -> str:
        lines = []
        for name, data in metrics.items():
            change = f" ({'+' if data['change_pct'] > 0 else ''}{data['change_pct']}%)" if data.get("change_pct") else ""
            lines.append(f"  {name}: {data['value']} {data.get('unit', '')}{change}")
        return "\n".join(lines) if lines else "  No metrics recorded yet."

    async def record_metric(self, db: AsyncSession, name: str, value: float,
                            unit: str = "", period: str = "", source: str = "manual") -> dict:
        """Record a business metric."""
        if not period:
            period = datetime.utcnow().strftime("%Y-%m-%d")

        metric = BusinessMetric(
            metric_name=name,
            metric_value=value,
            metric_unit=unit,
            period=period,
            source=source,
        )
        db.add(metric)
        await db.commit()
        return {"id": metric.id, "name": name, "value": value}


cockpit_agent = ExecutiveCockpitAgent()
