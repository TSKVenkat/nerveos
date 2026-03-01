"""Email Agent — classifies, triages, drafts replies, manages follow-ups."""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from loguru import logger

from models.models import (
    EmailMessage, EmailAccount, DraftReply, Contact,
    Alert, AuditLog, EmailCategory, EmailPriority,
    AlertSeverity, ActionStatus
)
from services.email_service import email_service
from services.llm import llm_service


class EmailAgent:
    """
    Autonomous email assistant.

    Capabilities:
    - Fetch and sync emails from IMAP
    - AI-classify emails (lead, complaint, renewal risk, partnership, spam)
    - Prioritize inbox
    - Draft reply options for each email
    - Track follow-ups and send reminders
    """

    AGENT_NAME = "email_agent"

    CATEGORY_LIST = [c.value for c in EmailCategory]
    PRIORITY_LIST = [p.value for p in EmailPriority]

    async def sync_inbox(self, db: AsyncSession, account_id: int = None) -> dict:
        """Fetch new emails and process them."""
        logger.info("📧 Email Agent: Syncing inbox...")

        # Get all active accounts or a specific one
        query = select(EmailAccount).where(EmailAccount.is_active == True)
        if account_id:
            query = query.where(EmailAccount.id == account_id)
        result = await db.execute(query)
        accounts = result.scalars().all()

        total_new = 0
        total_processed = 0

        for account in accounts:
            raw_emails = await email_service.fetch_emails(
                host=account.imap_host,
                port=account.imap_port,
                user=account.username,
                password=account.password_encrypted,  # In prod, decrypt this
                limit=30,
            )

            for raw in raw_emails:
                # Check if already exists
                existing = await db.execute(
                    select(EmailMessage).where(
                        EmailMessage.message_id == raw["message_id"]
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                total_new += 1

                # Create email record
                em = EmailMessage(
                    account_id=account.id,
                    message_id=raw["message_id"],
                    from_address=raw["from"],
                    to_address=raw["to"],
                    subject=raw["subject"],
                    body_text=raw["body_text"],
                    body_html=raw["body_html"],
                    received_at=datetime.fromisoformat(raw["date"]) if raw.get("date") else datetime.utcnow(),
                )
                db.add(em)
                await db.flush()

                # AI classification
                await self._classify_email(em)
                total_processed += 1

            account.last_sync = datetime.utcnow()

        await db.commit()
        logger.info("✅ Email Agent: {} new emails, {} processed", total_new, total_processed)
        return {"new": total_new, "processed": total_processed}

    async def _classify_email(self, email_msg: EmailMessage):
        """Classify and prioritize an email using LLM."""
        content = f"Subject: {email_msg.subject}\n\nBody: {email_msg.body_text[:1500]}"

        # Classify category
        category = await llm_service.classify(content, self.CATEGORY_LIST)
        email_msg.category = EmailCategory(category) if category in self.CATEGORY_LIST else EmailCategory.GENERAL

        # Classify priority
        priority = await llm_service.classify(
            f"Urgency level of this email:\n{content[:1000]}",
            self.PRIORITY_LIST
        )
        email_msg.priority = EmailPriority(priority) if priority in self.PRIORITY_LIST else EmailPriority.MEDIUM

        # Generate summary
        email_msg.ai_summary = await llm_service.summarize(content)

        # Determine if reply needed
        email_msg.needs_reply = email_msg.category not in [EmailCategory.SPAM, EmailCategory.GENERAL]

    async def draft_replies(self, db: AsyncSession, email_id: int, tones: list[str] = None) -> list[dict]:
        """Generate multiple draft replies for an email."""
        if tones is None:
            tones = ["professional", "friendly", "concise"]

        result = await db.execute(
            select(EmailMessage).where(EmailMessage.id == email_id)
        )
        email_msg = result.scalar_one_or_none()
        if not email_msg:
            return []

        drafts = []
        for tone in tones:
            body = await llm_service.draft_email_reply(
                email_msg.subject,
                email_msg.body_text,
                tone=tone,
            )
            draft = DraftReply(
                email_id=email_id,
                tone=tone,
                body=body,
                status=ActionStatus.PENDING,
            )
            db.add(draft)
            drafts.append({"tone": tone, "body": body})

        await db.commit()
        return drafts

    async def approve_and_send(self, db: AsyncSession, draft_id: int, approved_by: str = "user") -> dict:
        """Approve a draft and send it."""
        result = await db.execute(
            select(DraftReply).where(DraftReply.id == draft_id)
        )
        draft = result.scalar_one_or_none()
        if not draft:
            return {"error": "Draft not found"}

        # Get the original email
        result = await db.execute(
            select(EmailMessage).where(EmailMessage.id == draft.email_id)
        )
        email_msg = result.scalar_one_or_none()
        if not email_msg:
            return {"error": "Original email not found"}

        # Get the account
        result = await db.execute(
            select(EmailAccount).where(EmailAccount.id == email_msg.account_id)
        )
        account = result.scalar_one_or_none()

        if account:
            success = await email_service.send_email(
                to=email_msg.from_address,
                subject=f"Re: {email_msg.subject}",
                body=draft.body,
                host=account.smtp_host,
                port=account.smtp_port,
                user=account.username,
                password=account.password_encrypted,
            )
        else:
            success = False

        draft.status = ActionStatus.EXECUTED if success else ActionStatus.FAILED
        draft.approved_by = approved_by
        draft.sent_at = datetime.utcnow() if success else None

        # Audit log
        audit = AuditLog(
            agent_name=self.AGENT_NAME,
            action="send_reply",
            entity_type="draft_reply",
            entity_id=draft_id,
            input_data={"to": email_msg.from_address, "subject": email_msg.subject},
            output_data={"success": success},
            user_approved=True,
            approved_by=approved_by,
            status="executed" if success else "failed",
        )
        db.add(audit)
        await db.commit()

        return {"success": success, "draft_id": draft_id}

    async def get_inbox_summary(self, db: AsyncSession) -> dict:
        """Get a summary of the inbox state."""
        # Unread count by category
        result = await db.execute(select(EmailMessage).where(EmailMessage.is_read == False))
        unread = result.scalars().all()

        by_category = {}
        by_priority = {}
        needs_reply = 0

        for em in unread:
            cat = em.category.value if em.category else "general"
            pri = em.priority.value if em.priority else "medium"
            by_category[cat] = by_category.get(cat, 0) + 1
            by_priority[pri] = by_priority.get(pri, 0) + 1
            if em.needs_reply:
                needs_reply += 1

        return {
            "total_unread": len(unread),
            "by_category": by_category,
            "by_priority": by_priority,
            "needs_reply": needs_reply,
        }

    async def check_follow_ups(self, db: AsyncSession) -> list[dict]:
        """Check for emails that need follow-up."""
        cutoff = datetime.utcnow() - timedelta(days=3)
        result = await db.execute(
            select(EmailMessage).where(
                and_(
                    EmailMessage.needs_reply == True,
                    EmailMessage.reply_drafted == False,
                    EmailMessage.received_at <= cutoff,
                )
            )
        )
        stale = result.scalars().all()

        alerts = []
        for em in stale:
            alert = Alert(
                title=f"Follow-up needed: {em.subject[:100]}",
                message=f"Email from {em.from_address} received on {em.received_at} has no reply.",
                severity=AlertSeverity.WARNING,
                source=self.AGENT_NAME,
                related_entity_type="email",
                related_entity_id=em.id,
            )
            db.add(alert)
            alerts.append({
                "email_id": em.id,
                "subject": em.subject,
                "from": em.from_address,
                "days_old": (datetime.utcnow() - em.received_at).days,
            })

        await db.commit()
        return alerts


email_agent = EmailAgent()
