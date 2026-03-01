"""Policy Engine — guardrails for autonomous agent actions."""

from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from models.models import PolicyRule, SuggestedAction, AuditLog, ActionStatus
from config import settings


class PolicyEngine:
    """
    Evaluates whether an action should be auto-approved, require human review, or be blocked.

    Default policies:
    - All email sends require approval
    - Deal changes above threshold require manager approval
    - Read-only actions (search, analysis) can be auto-approved
    - Everything is logged to audit trail
    """

    SAFE_ACTIONS = {"search", "analyze", "generate_report", "classify", "summarize", "review_analysis"}
    REQUIRES_APPROVAL = {"send_email", "update_deal", "create_campaign", "change_stage"}
    BLOCKED_ACTIONS = set()  # Can be configured

    async def evaluate(self, db: AsyncSession, action: SuggestedAction) -> dict:
        """
        Evaluate an action against policies.
        Returns: {"decision": "approve"|"require_approval"|"block", "reason": str}
        """
        action_type = action.action_type

        # Check custom policies first
        custom_decision = await self._check_custom_policies(db, action)
        if custom_decision:
            return custom_decision

        # Built-in policy checks
        if action_type in self.BLOCKED_ACTIONS:
            return {
                "decision": "block",
                "reason": f"Action type '{action_type}' is blocked by policy.",
            }

        if settings.AUTO_APPROVE_SAFE_ACTIONS and action_type in self.SAFE_ACTIONS:
            return {
                "decision": "approve",
                "reason": "Safe action auto-approved.",
            }

        if action_type in self.REQUIRES_APPROVAL:
            # Check deal value threshold
            params = action.parameters or {}
            deal_value = params.get("deal_value", 0)
            if deal_value > settings.MAX_DEAL_VALUE_AUTO_APPROVE:
                return {
                    "decision": "require_approval",
                    "reason": f"Deal value {deal_value} exceeds auto-approve threshold {settings.MAX_DEAL_VALUE_AUTO_APPROVE}.",
                }
            return {
                "decision": "require_approval",
                "reason": f"Action type '{action_type}' requires human approval.",
            }

        # Default: require approval for safety
        return {
            "decision": "require_approval",
            "reason": "Default policy: all actions require approval.",
        }

    async def _check_custom_policies(self, db: AsyncSession, action: SuggestedAction) -> Optional[dict]:
        """Check custom policy rules from database."""
        result = await db.execute(
            select(PolicyRule)
            .where(PolicyRule.is_active == True)
            .order_by(PolicyRule.priority.desc())
        )
        rules = result.scalars().all()

        for rule in rules:
            conditions = rule.conditions or {}

            # Match action type
            if "action_type" in conditions and conditions["action_type"] != action.action_type:
                continue

            # Match deal value
            params = action.parameters or {}
            if "deal_value_gt" in conditions:
                if params.get("deal_value", 0) <= conditions["deal_value_gt"]:
                    continue

            if "deal_value_lt" in conditions:
                if params.get("deal_value", 0) >= conditions["deal_value_lt"]:
                    continue

            # Rule matched
            decision_map = {
                "block": "block",
                "require_approval": "require_approval",
                "auto_approve": "approve",
            }
            return {
                "decision": decision_map.get(rule.rule_type, "require_approval"),
                "reason": f"Policy '{rule.name}': {rule.description}",
                "policy_id": rule.id,
            }

        return None

    async def approve_action(self, db: AsyncSession, action_id: int, approved_by: str = "user") -> dict:
        """Approve a pending action."""
        result = await db.execute(
            select(SuggestedAction).where(SuggestedAction.id == action_id)
        )
        action = result.scalar_one_or_none()
        if not action:
            return {"error": "Action not found"}

        if action.status != ActionStatus.PENDING:
            return {"error": f"Action is already {action.status.value}"}

        action.status = ActionStatus.APPROVED
        action.approved_by = approved_by

        # Log to audit trail
        await self._audit_log(db, "approve_action", "suggested_action", action_id,
                              {"approved_by": approved_by}, {"status": "approved"}, True, approved_by)

        await db.commit()
        return {"success": True, "action_id": action_id, "status": "approved"}

    async def reject_action(self, db: AsyncSession, action_id: int, rejected_by: str = "user", reason: str = "") -> dict:
        """Reject a pending action."""
        result = await db.execute(
            select(SuggestedAction).where(SuggestedAction.id == action_id)
        )
        action = result.scalar_one_or_none()
        if not action:
            return {"error": "Action not found"}

        action.status = ActionStatus.REJECTED

        await self._audit_log(db, "reject_action", "suggested_action", action_id,
                              {"rejected_by": rejected_by, "reason": reason},
                              {"status": "rejected"}, False, rejected_by)

        await db.commit()
        return {"success": True, "action_id": action_id, "status": "rejected"}

    async def _audit_log(self, db: AsyncSession, action: str, entity_type: str, entity_id: int,
                         input_data: dict, output_data: dict, user_approved: bool, approved_by: str):
        log = AuditLog(
            agent_name="policy_engine",
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            input_data=input_data,
            output_data=output_data,
            user_approved=user_approved,
            approved_by=approved_by,
            status="completed",
        )
        db.add(log)

    async def get_pending_actions(self, db: AsyncSession) -> list[dict]:
        """Get all actions awaiting approval."""
        result = await db.execute(
            select(SuggestedAction)
            .where(SuggestedAction.status == ActionStatus.PENDING)
            .order_by(SuggestedAction.created_at.desc())
        )
        actions = result.scalars().all()
        return [
            {
                "id": a.id,
                "action_type": a.action_type,
                "title": a.title,
                "description": a.description[:300] if a.description else "",
                "requires_approval": a.requires_approval,
                "created_at": a.created_at.isoformat(),
            }
            for a in actions
        ]

    async def get_audit_trail(self, db: AsyncSession, limit: int = 50) -> list[dict]:
        """Get recent audit logs."""
        result = await db.execute(
            select(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        logs = result.scalars().all()
        return [
            {
                "id": l.id,
                "agent": l.agent_name,
                "action": l.action,
                "entity_type": l.entity_type,
                "entity_id": l.entity_id,
                "user_approved": l.user_approved,
                "approved_by": l.approved_by,
                "status": l.status,
                "created_at": l.created_at.isoformat(),
            }
            for l in logs
        ]


policy_engine = PolicyEngine()
