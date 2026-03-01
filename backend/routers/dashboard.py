"""Executive Dashboard API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from agents.executive_cockpit import cockpit_agent
from agents.orchestrator import orchestrator

router = APIRouter(prefix="/api/dashboard", tags=["Executive Dashboard"])


@router.get("/")
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Full executive dashboard."""
    return await cockpit_agent.get_dashboard(db)


@router.get("/anomalies")
async def check_anomalies(db: AsyncSession = Depends(get_db)):
    """Check for metric anomalies."""
    return await cockpit_agent.check_metric_anomalies(db)


@router.post("/metrics")
async def record_metric(data: dict, db: AsyncSession = Depends(get_db)):
    """Record a business metric."""
    return await cockpit_agent.record_metric(
        db,
        name=data["name"],
        value=data["value"],
        unit=data.get("unit", ""),
        period=data.get("period", ""),
        source=data.get("source", "manual"),
    )


@router.post("/ask")
async def ask_question(data: dict, db: AsyncSession = Depends(get_db)):
    """Natural language query about business data."""
    answer = await orchestrator.ask(db, data["question"])
    return {"question": data["question"], "answer": answer}


@router.post("/briefing")
async def morning_briefing(db: AsyncSession = Depends(get_db)):
    """Generate complete morning briefing."""
    return await orchestrator.morning_briefing(db)
