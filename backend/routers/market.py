"""Market Intelligence API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional

from database import get_db
from models.models import Competitor, MarketIntelReport, WatchedTopic
from agents.market_intel import market_intel_agent
from services.trends import trends_service
from services.finance import finance_service

router = APIRouter(prefix="/api/market", tags=["Market Intelligence"])


# ── Competitors CRUD ──────────────────────────────────────

@router.get("/competitors")
async def list_competitors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Competitor).order_by(Competitor.name))
    competitors = result.scalars().all()
    return [
        {
            "id": c.id, "name": c.name, "domain": c.domain,
            "keywords": c.keywords, "ticker_symbol": c.ticker_symbol,
            "track_trends": c.track_trends, "track_news": c.track_news,
            "track_finance": c.track_finance,
        }
        for c in competitors
    ]


@router.post("/competitors")
async def add_competitor(data: dict, db: AsyncSession = Depends(get_db)):
    comp = Competitor(
        name=data["name"],
        domain=data.get("domain", ""),
        description=data.get("description", ""),
        keywords=data.get("keywords", []),
        ticker_symbol=data.get("ticker_symbol", ""),
        track_trends=data.get("track_trends", True),
        track_news=data.get("track_news", True),
        track_finance=data.get("track_finance", bool(data.get("ticker_symbol"))),
    )
    db.add(comp)
    await db.commit()
    return {"id": comp.id, "name": comp.name}


@router.delete("/competitors/{comp_id}")
async def delete_competitor(comp_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Competitor).where(Competitor.id == comp_id))
    comp = result.scalar_one_or_none()
    if comp:
        await db.delete(comp)
        await db.commit()
        return {"deleted": True}
    return {"error": "Not found"}


# ── Watched Topics ────────────────────────────────────────

@router.get("/topics")
async def list_topics(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WatchedTopic))
    topics = result.scalars().all()
    return [
        {"id": t.id, "topic": t.topic, "topic_type": t.topic_type,
         "track_trends": t.track_trends, "track_news": t.track_news}
        for t in topics
    ]


@router.post("/topics")
async def add_topic(data: dict, db: AsyncSession = Depends(get_db)):
    topic = WatchedTopic(
        topic=data["topic"],
        topic_type=data.get("topic_type", "keyword"),
        track_trends=data.get("track_trends", True),
        track_news=data.get("track_news", True),
        track_finance=data.get("track_finance", False),
    )
    db.add(topic)
    await db.commit()
    return {"id": topic.id, "topic": topic.topic}


# ── Intelligence Reports ─────────────────────────────────

@router.get("/reports")
async def list_reports(
    limit: int = Query(default=30, le=100),
    report_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(MarketIntelReport).order_by(desc(MarketIntelReport.created_at)).limit(limit)
    if report_type:
        query = query.where(MarketIntelReport.report_type == report_type)
    result = await db.execute(query)
    reports = result.scalars().all()
    return [
        {
            "id": r.id, "type": r.report_type, "title": r.title,
            "summary": r.summary, "severity": r.severity.value if r.severity else "info",
            "is_read": r.is_read, "created_at": r.created_at.isoformat(),
            "competitor_id": r.competitor_id,
            "data": r.raw_data,
        }
        for r in reports
    ]


@router.post("/reports/{report_id}/read")
async def mark_read(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MarketIntelReport).where(MarketIntelReport.id == report_id))
    report = result.scalar_one_or_none()
    if report:
        report.is_read = True
        await db.commit()
        return {"success": True}
    return {"error": "Not found"}


# ── Scans & Actions ───────────────────────────────────────

@router.post("/scan")
async def run_scan(db: AsyncSession = Depends(get_db)):
    """Trigger a full market intelligence scan."""
    reports = await market_intel_agent.run_full_scan(db)
    return {"reports_generated": len(reports), "details": reports}


@router.post("/scan/competitor/{comp_id}")
async def scan_competitor(comp_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Competitor).where(Competitor.id == comp_id))
    comp = result.scalar_one_or_none()
    if not comp:
        return {"error": "Competitor not found"}
    reports = await market_intel_agent.scan_competitor(db, comp)
    await db.commit()
    return {"reports": reports}


@router.get("/digest")
async def get_digest(days: int = Query(default=1), db: AsyncSession = Depends(get_db)):
    digest = await market_intel_agent.generate_digest(db, days=days)
    return {"digest": digest}


@router.get("/search")
async def quick_search(q: str = Query(...), db: AsyncSession = Depends(get_db)):
    results = await market_intel_agent.quick_search(q)
    return results


# ── Direct Service Access ─────────────────────────────────

@router.get("/trends")
async def get_trends(keywords: str = Query(..., description="Comma-separated keywords")):
    kw_list = [k.strip() for k in keywords.split(",")][:5]
    data = await trends_service.get_interest_over_time(kw_list)
    return data


@router.get("/trends/trending")
async def get_trending(country: str = Query(default="india")):
    data = await trends_service.get_trending_searches(country)
    return {"trending": data}


@router.get("/finance/{ticker}")
async def get_stock(ticker: str):
    info = await finance_service.get_stock_info(ticker)
    return info


@router.get("/finance/{ticker}/history")
async def get_stock_history(ticker: str, period: str = Query(default="3mo")):
    data = await finance_service.get_price_history(ticker, period)
    return data


@router.get("/finance/{ticker}/anomalies")
async def get_anomalies(ticker: str):
    data = await finance_service.detect_anomalies(ticker)
    return data
