"""Email Agent API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional

from database import get_db
from models.models import EmailMessage, EmailAccount, DraftReply, Contact, EmailCategory
from agents.email_agent import email_agent

router = APIRouter(prefix="/api/email", tags=["Email Agent"])


# ── Email Accounts ────────────────────────────────────────

@router.get("/accounts")
async def list_accounts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EmailAccount))
    accounts = result.scalars().all()
    return [
        {
            "id": a.id, "email": a.email_address, "display_name": a.display_name,
            "is_active": a.is_active,
            "last_sync": a.last_sync.isoformat() if a.last_sync else None,
        }
        for a in accounts
    ]


@router.post("/accounts")
async def add_account(data: dict, db: AsyncSession = Depends(get_db)):
    account = EmailAccount(
        email_address=data["email"],
        display_name=data.get("display_name", data["email"]),
        imap_host=data.get("imap_host", ""),
        imap_port=data.get("imap_port", 993),
        smtp_host=data.get("smtp_host", ""),
        smtp_port=data.get("smtp_port", 587),
        username=data.get("username", data["email"]),
        password_encrypted=data.get("password", ""),  # In prod, encrypt this
    )
    db.add(account)
    await db.commit()
    return {"id": account.id, "email": account.email_address}


# ── Inbox ─────────────────────────────────────────────────

@router.get("/inbox")
async def get_inbox(
    limit: int = Query(default=30, le=100),
    category: Optional[str] = None,
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    query = select(EmailMessage).order_by(desc(EmailMessage.received_at)).limit(limit)
    if category:
        query = query.where(EmailMessage.category == EmailCategory(category))
    if unread_only:
        query = query.where(EmailMessage.is_read == False)
    result = await db.execute(query)
    emails = result.scalars().all()
    return [
        {
            "id": e.id, "from": e.from_address, "to": e.to_address,
            "subject": e.subject, "summary": e.ai_summary,
            "category": e.category.value if e.category else "general",
            "priority": e.priority.value if e.priority else "medium",
            "is_read": e.is_read, "needs_reply": e.needs_reply,
            "received_at": e.received_at.isoformat() if e.received_at else "",
        }
        for e in emails
    ]


@router.get("/inbox/summary")
async def inbox_summary(db: AsyncSession = Depends(get_db)):
    return await email_agent.get_inbox_summary(db)


@router.get("/inbox/{email_id}")
async def get_email_detail(email_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EmailMessage).where(EmailMessage.id == email_id))
    em = result.scalar_one_or_none()
    if not em:
        return {"error": "Not found"}
    em.is_read = True
    await db.commit()
    return {
        "id": em.id, "from": em.from_address, "to": em.to_address,
        "subject": em.subject, "body": em.body_text,
        "summary": em.ai_summary,
        "category": em.category.value if em.category else "general",
        "priority": em.priority.value if em.priority else "medium",
        "needs_reply": em.needs_reply,
        "received_at": em.received_at.isoformat() if em.received_at else "",
    }


# ── Drafts & Replies ─────────────────────────────────────

@router.post("/inbox/{email_id}/draft")
async def generate_drafts(email_id: int, data: dict = None, db: AsyncSession = Depends(get_db)):
    tones = (data or {}).get("tones", ["professional", "friendly", "concise"])
    drafts = await email_agent.draft_replies(db, email_id, tones)
    return {"drafts": drafts}


@router.get("/drafts")
async def list_drafts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DraftReply).order_by(desc(DraftReply.created_at)).limit(50)
    )
    drafts = result.scalars().all()
    return [
        {
            "id": d.id, "email_id": d.email_id, "tone": d.tone,
            "body": d.body[:300], "status": d.status.value if d.status else "pending",
            "created_at": d.created_at.isoformat(),
        }
        for d in drafts
    ]


@router.post("/drafts/{draft_id}/approve")
async def approve_draft(draft_id: int, db: AsyncSession = Depends(get_db)):
    return await email_agent.approve_and_send(db, draft_id)


@router.post("/drafts/{draft_id}/reject")
async def reject_draft(draft_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DraftReply).where(DraftReply.id == draft_id))
    draft = result.scalar_one_or_none()
    if draft:
        from models.models import ActionStatus
        draft.status = ActionStatus.REJECTED
        await db.commit()
        return {"success": True}
    return {"error": "Not found"}


# ── Sync & Follow-ups ────────────────────────────────────

@router.post("/sync")
async def sync_emails(db: AsyncSession = Depends(get_db)):
    return await email_agent.sync_inbox(db)


@router.get("/follow-ups")
async def check_follow_ups(db: AsyncSession = Depends(get_db)):
    return await email_agent.check_follow_ups(db)


# ── Contacts / CRM ───────────────────────────────────────

@router.get("/contacts")
async def list_contacts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Contact).order_by(Contact.name))
    contacts = result.scalars().all()
    return [
        {
            "id": c.id, "name": c.name, "email": c.email,
            "company": c.company, "role": c.role,
            "deal_value": c.deal_value, "deal_stage": c.deal_stage,
            "tags": c.tags,
        }
        for c in contacts
    ]


@router.post("/contacts")
async def add_contact(data: dict, db: AsyncSession = Depends(get_db)):
    contact = Contact(
        name=data["name"],
        email=data.get("email", ""),
        company=data.get("company", ""),
        role=data.get("role", ""),
        phone=data.get("phone", ""),
        tags=data.get("tags", []),
        deal_value=data.get("deal_value", 0),
        deal_stage=data.get("deal_stage", "new"),
        notes=data.get("notes", ""),
    )
    db.add(contact)
    await db.commit()
    return {"id": contact.id, "name": contact.name}


@router.put("/contacts/{contact_id}")
async def update_contact(contact_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        return {"error": "Not found"}
    for key, val in data.items():
        if hasattr(contact, key):
            setattr(contact, key, val)
    await db.commit()
    return {"success": True, "id": contact_id}
