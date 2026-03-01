"""Actions & Guardrails API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from guardrails.policy_engine import policy_engine
from models.models import PolicyRule

from sqlalchemy import select

router = APIRouter(prefix="/api/actions", tags=["Actions & Guardrails"])


@router.get("/pending")
async def get_pending_actions(db: AsyncSession = Depends(get_db)):
    return await policy_engine.get_pending_actions(db)


@router.post("/{action_id}/approve")
async def approve_action(action_id: int, db: AsyncSession = Depends(get_db)):
    return await policy_engine.approve_action(db, action_id)


@router.post("/{action_id}/reject")
async def reject_action(action_id: int, data: dict = None, db: AsyncSession = Depends(get_db)):
    reason = (data or {}).get("reason", "")
    return await policy_engine.reject_action(db, action_id, reason=reason)


@router.get("/audit")
async def get_audit_trail(db: AsyncSession = Depends(get_db)):
    return await policy_engine.get_audit_trail(db)


# ── Policy Rules ──────────────────────────────────────────

@router.get("/policies")
async def list_policies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PolicyRule).order_by(PolicyRule.priority.desc()))
    rules = result.scalars().all()
    return [
        {
            "id": r.id, "name": r.name, "description": r.description,
            "rule_type": r.rule_type, "conditions": r.conditions,
            "is_active": r.is_active, "priority": r.priority,
        }
        for r in rules
    ]


@router.post("/policies")
async def add_policy(data: dict, db: AsyncSession = Depends(get_db)):
    rule = PolicyRule(
        name=data["name"],
        description=data.get("description", ""),
        rule_type=data.get("rule_type", "require_approval"),
        conditions=data.get("conditions", {}),
        is_active=data.get("is_active", True),
        priority=data.get("priority", 0),
    )
    db.add(rule)
    await db.commit()
    return {"id": rule.id, "name": rule.name}


@router.delete("/policies/{policy_id}")
async def delete_policy(policy_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PolicyRule).where(PolicyRule.id == policy_id))
    rule = result.scalar_one_or_none()
    if rule:
        await db.delete(rule)
        await db.commit()
        return {"deleted": True}
    return {"error": "Not found"}
