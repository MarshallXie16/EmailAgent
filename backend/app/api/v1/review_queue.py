"""Review queue endpoints."""

from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_current_broker
from app.core.database import get_db
from app.models.broker import Broker
from app.models.email import EmailThread, EmailMessage, ThreadStatus, MessageDirection, MessageSentBy
from app.models.agent import AgentRun
from app.models.lead import Lead
from app.models.listing import Listing
from app.services.gmail import GmailService
from app.schemas.review_queue import (
    ReviewQueueResponse,
    ReviewQueueItem,
    ReviewQueueLeadInfo,
    ReviewQueueListingInfo,
    ReviewQueueMessagePreview,
    AgentReasoningDetail,
    ApproveEmailRequest,
    ManualReplyRequest,
)

router = APIRouter()


@router.get("", response_model=ReviewQueueResponse)
async def get_review_queue(
    current_broker: Broker = Depends(get_current_broker),
    db: AsyncSession = Depends(get_db),
):
    """
    Get threads that require broker review.

    Returns threads with status=needs_broker or requires_review=true,
    sorted by priority score (descending).

    Args:
        current_broker: Authenticated broker
        db: Database session

    Returns:
        List of threads needing review
    """
    # Query threads needing review
    query = (
        select(EmailThread)
        .options(
            selectinload(EmailThread.messages),
            selectinload(EmailThread.agent_runs),
            selectinload(EmailThread.lead),
            selectinload(EmailThread.listing),
        )
        .where(
            and_(
                EmailThread.broker_id == current_broker.id,
                (
                    (EmailThread.status == ThreadStatus.NEEDS_BROKER)
                    | (EmailThread.requires_review == True)
                ),
            )
        )
        .order_by(desc(EmailThread.priority_score))
    )

    result = await db.execute(query)
    threads = result.scalars().all()

    # Build response items
    items = []
    for thread in threads:
        # Get last inbound message
        inbound_messages = [
            msg for msg in thread.messages
            if msg.direction == MessageDirection.INBOUND
        ]
        if not inbound_messages:
            continue

        last_inbound = max(inbound_messages, key=lambda m: m.sent_at)

        # Get most recent agent run
        if not thread.agent_runs:
            continue

        latest_agent_run = max(thread.agent_runs, key=lambda r: r.created_at)

        # Extract reasoning
        reasoning_data = latest_agent_run.reasoning or {}
        why_flagged = reasoning_data.get("why_flagged", "Agent escalated this conversation")

        # Extract tools called
        tools_called = []
        if latest_agent_run.tools_called:
            if isinstance(latest_agent_run.tools_called, list):
                for tool in latest_agent_run.tools_called:
                    if isinstance(tool, dict):
                        tools_called.append(tool.get("name", "unknown"))
                    else:
                        tools_called.append(str(tool))

        agent_reasoning = AgentReasoningDetail(
            why_flagged=why_flagged,
            confidence=float(latest_agent_run.confidence_score or 0.0),
            concerns=reasoning_data.get("concerns", []),
            tools_called=tools_called,
            confidence_factors=reasoning_data.get("confidence_factors"),
        )

        # Build lead info
        lead_info = ReviewQueueLeadInfo(
            id=thread.lead.id,
            name=thread.lead.name,
            email=thread.lead.email,
            type=thread.lead.type.value,
        )

        # Build listing info
        listing_info = None
        if thread.listing:
            listing_info = ReviewQueueListingInfo(
                id=thread.listing.id,
                code=thread.listing.code,
                title=thread.listing.title,
                asking_price=thread.listing.asking_price,
            )

        # Build message preview
        last_inbound_preview = ReviewQueueMessagePreview(
            id=last_inbound.id,
            direction=last_inbound.direction.value,
            from_email=last_inbound.from_email,
            to_email=last_inbound.to_email,
            body_text=last_inbound.body_text,
            sent_at=last_inbound.sent_at,
            sent_by=last_inbound.sent_by.value,
        )

        items.append(
            ReviewQueueItem(
                id=thread.id,
                lead=lead_info,
                listing=listing_info,
                status=thread.status.value,
                last_inbound_message=last_inbound_preview,
                proposed_response=latest_agent_run.response,
                agent_reasoning=agent_reasoning,
                created_at=thread.created_at,
                priority_score=float(thread.priority_score),
                message_count=len(thread.messages),
            )
        )

    return ReviewQueueResponse(threads=items, total=len(items))


@router.post("/{thread_id}/approve", status_code=status.HTTP_200_OK)
async def approve_email(
    thread_id: UUID,
    request: ApproveEmailRequest,
    current_broker: Broker = Depends(get_current_broker),
    db: AsyncSession = Depends(get_db),
):
    """
    Approve and send agent's proposed response (optionally with edits).

    Args:
        thread_id: Email thread UUID
        request: Approval request with optional edits
        current_broker: Authenticated broker
        db: Database session

    Returns:
        Success message with sent email details
    """
    # Get thread
    result = await db.execute(
        select(EmailThread)
        .options(
            selectinload(EmailThread.messages),
            selectinload(EmailThread.agent_runs),
            selectinload(EmailThread.lead),
        )
        .where(
            and_(
                EmailThread.id == thread_id,
                EmailThread.broker_id == current_broker.id,
            )
        )
    )
    thread = result.scalar_one_or_none()

    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        )

    # Get latest agent run
    if not thread.agent_runs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No agent response found for this thread",
        )

    latest_agent_run = max(thread.agent_runs, key=lambda r: r.created_at)

    # Determine email body (original or edited)
    email_body = request.edits if request.edits else latest_agent_run.response

    # Get lead
    lead = thread.lead

    # Get subject from first message
    first_msg = min(thread.messages, key=lambda m: m.sent_at)
    subject = first_msg.subject or "Re: Inquiry"
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    # Send email via Gmail
    gmail_service = GmailService()
    sent_message_id = gmail_service.send_email(
        to=lead.email,
        subject=subject,
        body=email_body,
        thread_id=thread.external_thread_id,
    )

    if not sent_message_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email",
        )

    # Create outbound message record
    outbound_msg = EmailMessage(
        email_thread_id=thread.id,
        direction=MessageDirection.OUTBOUND,
        from_email=current_broker.email,
        to_email=lead.email,
        subject=subject,
        body_text=email_body,
        sent_at=datetime.utcnow(),
        sent_by=MessageSentBy.BROKER,
    )
    db.add(outbound_msg)

    # Update thread status
    thread.status = ThreadStatus.OPEN
    thread.requires_review = False
    thread.updated_at = datetime.utcnow()

    await db.commit()

    return {
        "status": "success",
        "message": "Email sent successfully",
        "thread_id": str(thread_id),
        "sent_to": lead.email,
        "edited": request.edits is not None,
    }


@router.post("/{thread_id}/manual-reply", status_code=status.HTTP_200_OK)
async def send_manual_reply(
    thread_id: UUID,
    request: ManualReplyRequest,
    current_broker: Broker = Depends(get_current_broker),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a manual reply, overriding agent's suggestion.

    Args:
        thread_id: Email thread UUID
        request: Manual reply request
        current_broker: Authenticated broker
        db: Database session

    Returns:
        Success message with sent email details
    """
    # Get thread
    result = await db.execute(
        select(EmailThread)
        .options(
            selectinload(EmailThread.messages),
            selectinload(EmailThread.lead),
        )
        .where(
            and_(
                EmailThread.id == thread_id,
                EmailThread.broker_id == current_broker.id,
            )
        )
    )
    thread = result.scalar_one_or_none()

    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        )

    # Get lead
    lead = thread.lead

    # Get subject from first message
    if thread.messages:
        first_msg = min(thread.messages, key=lambda m: m.sent_at)
        subject = first_msg.subject or "Re: Inquiry"
    else:
        subject = "Re: Inquiry"

    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    # Send email via Gmail
    gmail_service = GmailService()
    sent_message_id = gmail_service.send_email(
        to=lead.email,
        subject=subject,
        body=request.body_text,
        thread_id=thread.external_thread_id,
    )

    if not sent_message_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email",
        )

    # Create outbound message record
    outbound_msg = EmailMessage(
        email_thread_id=thread.id,
        direction=MessageDirection.OUTBOUND,
        from_email=current_broker.email,
        to_email=lead.email,
        subject=subject,
        body_text=request.body_text,
        sent_at=datetime.utcnow(),
        sent_by=MessageSentBy.BROKER,
    )
    db.add(outbound_msg)

    # Update thread status
    thread.status = ThreadStatus.OPEN
    thread.requires_review = False
    thread.updated_at = datetime.utcnow()

    await db.commit()

    return {
        "status": "success",
        "message": "Manual reply sent successfully",
        "thread_id": str(thread_id),
        "sent_to": lead.email,
    }


@router.post("/{thread_id}/mark-resolved", status_code=status.HTTP_200_OK)
async def mark_thread_resolved(
    thread_id: UUID,
    current_broker: Broker = Depends(get_current_broker),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a thread as resolved without sending an email.

    Use when the issue was resolved outside of the system or no response is needed.

    Args:
        thread_id: Email thread UUID
        current_broker: Authenticated broker
        db: Database session

    Returns:
        Success message
    """
    # Get thread
    result = await db.execute(
        select(EmailThread).where(
            and_(
                EmailThread.id == thread_id,
                EmailThread.broker_id == current_broker.id,
            )
        )
    )
    thread = result.scalar_one_or_none()

    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        )

    # Update thread status
    thread.status = ThreadStatus.CLOSED
    thread.requires_review = False
    thread.updated_at = datetime.utcnow()

    await db.commit()

    return {
        "status": "success",
        "message": "Thread marked as resolved",
        "thread_id": str(thread_id),
    }
