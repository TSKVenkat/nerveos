"""Market Intelligence Agent — monitors competitors, trends, news, and finance."""

import asyncio
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from models.models import (
    Competitor, MarketIntelReport, WatchedTopic,
    SuggestedAction, AlertSeverity, ActionStatus
)
from services.searxng import searxng_service
from services.trends import trends_service
from services.news import news_service
from services.finance import finance_service
from services.llm import llm_service


class MarketIntelAgent:
    """
    Autonomous agent that continuously monitors the market.
    
    Capabilities:
    - Track competitors via news, trends, and financial data
    - Monitor watched keywords/topics
    - Generate daily/weekly digests
    - Suggest response actions
    """

    AGENT_NAME = "market_intel"

    async def run_full_scan(self, db: AsyncSession) -> list[dict]:
        """Run a complete market intelligence scan for all tracked competitors and topics."""
        logger.info("🔍 Market Intel Agent: Starting full scan...")

        reports = []

        # 1. Scan competitors
        result = await db.execute(select(Competitor))
        competitors = result.scalars().all()
        for comp in competitors:
            comp_reports = await self.scan_competitor(db, comp)
            reports.extend(comp_reports)

        # 2. Scan watched topics
        result = await db.execute(select(WatchedTopic))
        topics = result.scalars().all()
        for topic in topics:
            topic_reports = await self.scan_topic(db, topic)
            reports.extend(topic_reports)

        # 3. Get trending searches
        try:
            trending = await trends_service.get_trending_searches("india")
            if trending:
                report = MarketIntelReport(
                    report_type="trending",
                    title="Today's Trending Searches (India)",
                    summary=", ".join(trending[:15]),
                    raw_data={"trending": trending},
                    severity=AlertSeverity.INFO,
                )
                db.add(report)
                reports.append({"type": "trending", "data": trending[:15]})
        except Exception as e:
            logger.error("Trending search error: {}", e)

        await db.commit()
        logger.info("✅ Market Intel Agent: Scan complete — {} reports generated", len(reports))
        return reports

    async def scan_competitor(self, db: AsyncSession, competitor: Competitor) -> list[dict]:
        """Deep scan a single competitor."""
        reports = []

        # Gather data in parallel
        tasks = {}
        if competitor.track_news:
            tasks["news"] = news_service.fetch_competitor_news(
                competitor.name, competitor.keywords or []
            )
            tasks["web"] = searxng_service.search_news(
                f"{competitor.name} company", max_results=5
            )
        if competitor.track_trends and competitor.keywords:
            tasks["trends"] = trends_service.get_interest_over_time(
                [competitor.name] + (competitor.keywords or [])[:4]
            )
        if competitor.track_finance and competitor.ticker_symbol:
            tasks["finance"] = finance_service.get_stock_info(competitor.ticker_symbol)
            tasks["anomalies"] = finance_service.detect_anomalies(competitor.ticker_symbol)

        # Await all
        results = {}
        for key, coro in tasks.items():
            try:
                results[key] = await coro
            except Exception as e:
                logger.error("Competitor scan {} error for {}: {}", key, competitor.name, e)
                results[key] = None

        # ── News report ──
        news_items = (results.get("news") or []) + (results.get("web") or [])
        if news_items:
            # De-duplicate
            seen = set()
            unique_news = []
            for n in news_items:
                key = n["title"].lower().strip()
                if key not in seen:
                    seen.add(key)
                    unique_news.append(n)

            report = MarketIntelReport(
                competitor_id=competitor.id,
                report_type="news",
                title=f"News digest: {competitor.name}",
                summary=f"Found {len(unique_news)} articles",
                raw_data={"articles": unique_news[:15]},
                severity=AlertSeverity.INFO,
            )
            db.add(report)
            reports.append({"type": "news", "competitor": competitor.name, "count": len(unique_news)})

        # ── Trends report ──
        trends_data = results.get("trends")
        if trends_data and trends_data.get("series"):
            report = MarketIntelReport(
                competitor_id=competitor.id,
                report_type="trends",
                title=f"Search trends: {competitor.name}",
                summary=f"Tracking {len(trends_data.get('series', {}))} keywords",
                raw_data=trends_data,
                severity=AlertSeverity.INFO,
            )
            db.add(report)
            reports.append({"type": "trends", "competitor": competitor.name})

        # ── Finance report ──
        finance_data = results.get("finance")
        anomalies = results.get("anomalies")
        if finance_data and not finance_data.get("error"):
            severity = AlertSeverity.INFO
            if anomalies and anomalies.get("anomalies"):
                severity = AlertSeverity.WARNING

            report = MarketIntelReport(
                competitor_id=competitor.id,
                report_type="finance",
                title=f"Financial snapshot: {competitor.name} ({competitor.ticker_symbol})",
                summary=f"Price: {finance_data.get('current_price', 'N/A')} | "
                        f"MCap: {finance_data.get('market_cap', 'N/A')}",
                raw_data={"stock": finance_data, "anomalies": anomalies},
                severity=severity,
            )
            db.add(report)
            reports.append({"type": "finance", "competitor": competitor.name})

        # ── AI Analysis & Suggested Actions ──
        if news_items or finance_data:
            try:
                analysis = await llm_service.analyze_competitor_intel(
                    competitor.name, news_items[:5], trends_data or {}
                )
                report = MarketIntelReport(
                    competitor_id=competitor.id,
                    report_type="ai_analysis",
                    title=f"AI Analysis: {competitor.name}",
                    summary=analysis[:1000],
                    raw_data={"full_analysis": analysis},
                    severity=AlertSeverity.INFO,
                )
                db.add(report)
                await db.flush()

                # Create a suggested action
                action = SuggestedAction(
                    report_id=report.id,
                    action_type="review_analysis",
                    title=f"Review competitor analysis for {competitor.name}",
                    description=analysis[:500],
                    status=ActionStatus.PENDING,
                    requires_approval=True,
                )
                db.add(action)
                reports.append({"type": "ai_analysis", "competitor": competitor.name})
            except Exception as e:
                logger.error("AI analysis error: {}", e)

        return reports

    async def scan_topic(self, db: AsyncSession, topic: WatchedTopic) -> list[dict]:
        """Scan a watched topic / keyword."""
        reports = []

        if topic.track_news:
            news = await news_service.fetch_news_for_query(topic.topic, max_results=10)
            if news:
                report = MarketIntelReport(
                    report_type="topic_news",
                    title=f"Topic update: {topic.topic}",
                    summary=f"{len(news)} new articles",
                    raw_data={"articles": news},
                    severity=AlertSeverity.INFO,
                )
                db.add(report)
                reports.append({"type": "topic_news", "topic": topic.topic})

        if topic.track_trends:
            trends = await trends_service.get_interest_over_time([topic.topic])
            if trends and trends.get("series"):
                report = MarketIntelReport(
                    report_type="topic_trends",
                    title=f"Trends: {topic.topic}",
                    summary=f"Search interest data collected",
                    raw_data=trends,
                    severity=AlertSeverity.INFO,
                )
                db.add(report)
                reports.append({"type": "topic_trends", "topic": topic.topic})

        return reports

    async def generate_digest(self, db: AsyncSession, days: int = 1) -> str:
        """Generate an AI-powered digest of recent intel."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)

        result = await db.execute(
            select(MarketIntelReport)
            .where(MarketIntelReport.created_at >= cutoff)
            .order_by(MarketIntelReport.created_at.desc())
            .limit(50)
        )
        reports = result.scalars().all()

        if not reports:
            return "No new intelligence reports in the last {} day(s).".format(days)

        context = "\n".join([
            f"- [{r.report_type}] {r.title}: {r.summary[:200]}"
            for r in reports
        ])

        digest = await llm_service.generate(
            f"Create a brief executive digest of the following market intelligence:\n\n{context}",
            system="You are a business intelligence analyst. Create a concise, prioritized digest with actionable insights."
        )
        return digest

    async def quick_search(self, query: str) -> dict:
        """Ad-hoc search across all sources."""
        news_task = news_service.fetch_news_for_query(query, max_results=5)
        web_task = searxng_service.search(query, max_results=5)
        
        news, web = await asyncio.gather(news_task, web_task, return_exceptions=True)
        
        return {
            "news": news if isinstance(news, list) else [],
            "web": web if isinstance(web, list) else [],
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
        }


market_intel_agent = MarketIntelAgent()
