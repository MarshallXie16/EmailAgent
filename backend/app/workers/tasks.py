"""Celery background tasks."""

import asyncio
from datetime import datetime, time as datetime_time
from typing import List, Dict, Any
import pytz

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.models.broker import Broker, BrokerSettings
from app.models.listing import ListingDocument, ListingDocumentChunk
from app.models.lead import Lead
from app.models.email import EmailThread, EmailMessage, ThreadStatus, MessageDirection, MessageSentBy, AgentAction
from app.models.agent import AgentRun, FinalAction
from app.services.gmail import GmailService
from app.services.s3 import S3Service
from app.services.document_processor import DocumentProcessor
from app.services.openai_service import OpenAIService
from app.services.agent import AgentService


def run_async(coro):
    """Helper to run async functions in sync Celery tasks."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


@shared_task(bind=True, max_retries=3)
def poll_gmail_task(self):
    """
    Poll Gmail for new messages and create email threads.

    Runs periodically (every 10 minutes by default).
    Retries up to 3 times on failure.
    """
    try:
        return run_async(_poll_gmail())
    except Exception as exc:
        # Retry after 60 seconds
        raise self.retry(exc=exc, countdown=60)


async def _poll_gmail():
    """Async implementation of Gmail polling."""
    gmail_service = GmailService()
    processed_count = 0

    async with AsyncSessionLocal() as db:
        # Get all brokers (in MVP, likely just one)
        result = await db.execute(select(Broker))
        brokers = result.scalars().all()

        for broker in brokers:
            # Get unprocessed messages
            messages = gmail_service.get_unprocessed_messages()

            for msg_summary in messages:
                try:
                    # Get full message details
                    message = gmail_service.get_message(msg_summary["id"])
                    if not message:
                        continue

                    # Parse message
                    parsed = gmail_service.parse_message(message)

                    # Skip if from broker's own email
                    if parsed["from"] == broker.email:
                        gmail_service.mark_as_processed(msg_summary["id"])
                        continue

                    # Get or create lead
                    lead = await _get_or_create_lead(
                        db, broker.id, parsed["from"], parsed.get("from")
                    )

                    # Get or create email thread
                    thread = await _get_or_create_thread(
                        db, broker.id, lead.id, parsed["thread_id"]
                    )

                    # Create email message record
                    email_msg = EmailMessage(
                        email_thread_id=thread.id,
                        direction=MessageDirection.INBOUND,
                        from_email=parsed["from"],
                        to_email=parsed["to"] or broker.email,
                        subject=parsed["subject"],
                        body_text=parsed["body_text"],
                        sent_at=datetime.utcnow(),  # Could parse from Date header
                        raw_metadata=parsed["raw_metadata"],
                        sent_by=MessageSentBy.LEAD,
                    )
                    db.add(email_msg)

                    # Update thread status
                    thread.status = ThreadStatus.OPEN
                    thread.updated_at = datetime.utcnow()

                    # Try to identify listing from email content
                    if not thread.listing_id:
                        await _try_identify_listing(db, thread, parsed["body_text"], broker.id)

                    await db.commit()

                    # Mark as processed in Gmail
                    gmail_service.mark_as_processed(msg_summary["id"])

                    processed_count += 1

                except Exception as e:
                    print(f"Error processing message {msg_summary['id']}: {str(e)}")
                    await db.rollback()
                    continue

    return {
        "status": "success",
        "processed_count": processed_count,
        "timestamp": datetime.utcnow().isoformat(),
    }


async def _get_or_create_lead(db, broker_id: str, email: str, name: str = None):
    """Get existing lead or create new one."""
    from app.models.lead import LeadType

    result = await db.execute(
        select(Lead).where(Lead.broker_id == broker_id, Lead.email == email)
    )
    lead = result.scalar_one_or_none()

    if not lead:
        lead = Lead(
            broker_id=broker_id,
            email=email,
            name=name or email.split("@")[0],
            type=LeadType.OTHER,
        )
        db.add(lead)
        await db.flush()

    return lead


async def _get_or_create_thread(db, broker_id: str, lead_id: str, external_thread_id: str):
    """Get existing thread or create new one."""
    result = await db.execute(
        select(EmailThread).where(EmailThread.external_thread_id == external_thread_id)
    )
    thread = result.scalar_one_or_none()

    if not thread:
        thread = EmailThread(
            broker_id=broker_id,
            lead_id=lead_id,
            external_thread_id=external_thread_id,
            status=ThreadStatus.OPEN,
            last_agent_action=AgentAction.NONE,
        )
        db.add(thread)
        await db.flush()

    return thread


async def _try_identify_listing(db, thread, email_text: str, broker_id: str):
    """Try to identify which listing the email is about."""
    from app.services.agent import AgentTools

    tools = AgentTools(db)
    result = await tools.identify_listing(email_text, broker_id)

    if result.get("listing_id") and result.get("confidence", 0) >= 0.5:
        thread.listing_id = result["listing_id"]


@shared_task(bind=True, max_retries=2)
def run_email_batch(self):
    """
    Process email threads in batch windows.

    Checks if current time is within any broker's batch window.
    If yes, processes all open threads for that broker.
    """
    try:
        return run_async(_run_email_batch())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=120)


async def _run_email_batch():
    """Async implementation of batch email processing."""
    processed_threads = 0
    now_utc = datetime.utcnow()

    async with AsyncSessionLocal() as db:
        # Get all brokers with their settings
        result = await db.execute(
            select(Broker)
            .options(selectinload(Broker.settings))
        )
        brokers = result.scalars().all()

        for broker in brokers:
            if not broker.settings:
                continue

            # Check if current time is within any batch window
            if not _is_within_batch_window(now_utc, broker.settings, broker.timezone):
                continue

            # Get open threads that need processing
            threads_result = await db.execute(
                select(EmailThread)
                .where(
                    EmailThread.broker_id == broker.id,
                    EmailThread.status == ThreadStatus.OPEN,
                )
                .options(selectinload(EmailThread.messages))
            )
            threads = threads_result.scalars().all()

            for thread in threads:
                # Check if there's a new inbound message since last outbound
                if not _has_new_inbound(thread):
                    continue

                try:
                    await _process_thread_with_agent(db, thread, broker)
                    processed_threads += 1

                except Exception as e:
                    print(f"Error processing thread {thread.id}: {str(e)}")
                    # Mark as needs broker attention
                    thread.status = ThreadStatus.NEEDS_BROKER
                    thread.last_agent_action = AgentAction.ESCALATED
                    await db.commit()
                    continue

    return {
        "status": "success",
        "processed_threads": processed_threads,
        "timestamp": datetime.utcnow().isoformat(),
    }


def _is_within_batch_window(now_utc: datetime, settings: BrokerSettings, broker_timezone: str) -> bool:
    """Check if current time is within any batch window."""
    # Convert UTC to broker's timezone
    tz = pytz.timezone(broker_timezone)
    now_local = now_utc.replace(tzinfo=pytz.UTC).astimezone(tz)
    current_time = now_local.time()

    for window in settings.batch_windows:
        start = datetime_time.fromisoformat(window["start"])
        end = datetime_time.fromisoformat(window["end"])

        if start <= current_time <= end:
            return True

    return False


def _has_new_inbound(thread: EmailThread) -> bool:
    """Check if thread has new inbound message since last outbound."""
    if not thread.messages:
        return False

    # Sort messages by sent_at
    sorted_messages = sorted(thread.messages, key=lambda m: m.sent_at)

    # Find last outbound message
    last_outbound_idx = None
    for i in range(len(sorted_messages) - 1, -1, -1):
        if sorted_messages[i].direction == MessageDirection.OUTBOUND:
            last_outbound_idx = i
            break

    # If no outbound messages, process if there are inbound messages
    if last_outbound_idx is None:
        return any(m.direction == MessageDirection.INBOUND for m in sorted_messages)

    # Check if there are inbound messages after last outbound
    return any(
        m.direction == MessageDirection.INBOUND
        for m in sorted_messages[last_outbound_idx + 1:]
    )


async def _process_thread_with_agent(db, thread: EmailThread, broker: Broker):
    """Process a thread with the AI agent."""
    # Build conversation history (last 10 messages)
    sorted_messages = sorted(thread.messages, key=lambda m: m.sent_at)
    recent_messages = sorted_messages[-settings.MAX_CONTEXT_MESSAGES:]

    conversation = [
        {
            "role": "user" if msg.direction == MessageDirection.INBOUND else "assistant",
            "content": msg.body_text,
        }
        for msg in recent_messages
    ]

    # Run agent
    agent_service = AgentService(db)
    result = await agent_service.generate_response(
        conversation,
        str(broker.id),
        str(thread.lead_id) if thread.lead_id else None,
    )

    # Create agent run record
    agent_run = AgentRun(
        email_thread_id=thread.id,
        llm_model=settings.DEFAULT_LLM_MODEL,
        prompt=agent_service.get_system_prompt(),
        response=result["response_text"],
        tools_called=result["tools_called"],
        confidence_score=result["confidence"],
        final_action=FinalAction(result["final_action"]),
        reasoning=result.get("reasoning", {}),  # Store detailed reasoning
        error_flag=False,
    )
    db.add(agent_run)

    # Calculate priority score (0-10, higher = more urgent)
    # Priority = (10 - confidence * 10) + urgency_bonus
    confidence = result["confidence"]
    priority_score = (1.0 - confidence) * 10  # Inverse of confidence (0-10)

    # Add urgency bonus based on message count (more follow-ups = higher priority)
    message_count = len(thread.messages)
    if message_count > 5:
        priority_score += 2.0
    elif message_count > 3:
        priority_score += 1.0

    # Cap at 10.0
    priority_score = min(10.0, priority_score)

    # Determine whether to send or draft
    if result["final_action"] == "escalate":
        thread.status = ThreadStatus.NEEDS_BROKER
        thread.last_agent_action = AgentAction.ESCALATED
        thread.requires_review = True
        thread.priority_score = priority_score
        # Don't send email, let broker handle

    elif broker.settings.auto_send_enabled:
        # Send email via Gmail
        await _send_agent_response(db, thread, result["response_text"], broker)
        thread.last_agent_action = AgentAction.AUTO_REPLY_SENT
        thread.requires_review = False

    else:
        # Create draft for broker review
        thread.last_agent_action = AgentAction.DRAFT_CREATED
        thread.requires_review = True  # Flag drafts for review
        thread.priority_score = priority_score
        # Draft is the last agent_run, broker can view and edit in UI

    thread.updated_at = datetime.utcnow()
    await db.commit()


async def _send_agent_response(db, thread: EmailThread, response_text: str, broker: Broker):
    """Send agent response via Gmail."""
    gmail_service = GmailService()

    # Get lead email
    result = await db.execute(select(Lead).where(Lead.id == thread.lead_id))
    lead = result.scalar_one()

    # Get subject from first message in thread
    first_msg = sorted(thread.messages, key=lambda m: m.sent_at)[0]
    subject = first_msg.subject
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    # Send email
    sent_message_id = gmail_service.send_email(
        to=lead.email,
        subject=subject,
        body=response_text,
        thread_id=thread.external_thread_id,
    )

    if sent_message_id:
        # Create outbound message record
        outbound_msg = EmailMessage(
            email_thread_id=thread.id,
            direction=MessageDirection.OUTBOUND,
            from_email=broker.email,
            to_email=lead.email,
            subject=subject,
            body_text=response_text,
            sent_at=datetime.utcnow(),
            sent_by=MessageSentBy.AGENT,
        )
        db.add(outbound_msg)


@shared_task(bind=True, max_retries=2)
def ingest_document_task(self, document_id: int):
    """
    Ingest a document: extract text, chunk, embed, and store in DB.

    Args:
        document_id: ID of the ListingDocument to ingest
    """
    try:
        return run_async(_ingest_document(document_id))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=120)


async def _ingest_document(document_id: int):
    """Async implementation of document ingestion."""
    async with AsyncSessionLocal() as db:
        # Get document
        result = await db.execute(
            select(ListingDocument).where(ListingDocument.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            return {"status": "error", "message": "Document not found"}

        try:
            # Download from S3
            s3_service = S3Service()
            file_content = s3_service.download_file(document.file_url)

            if not file_content:
                return {"status": "error", "message": "Failed to download file"}

            # Determine file type
            file_ext = document.file_url.split(".")[-1].lower()

            # Process document (extract and chunk)
            processor = DocumentProcessor()
            chunks = processor.process_document(
                file_content,
                file_ext,
                metadata={"document_id": document_id, "title": document.title},
            )

            # Generate embeddings
            openai_service = OpenAIService()
            chunk_texts = [chunk["content"] for chunk in chunks]
            embeddings = openai_service.create_embeddings_batch(chunk_texts)

            # Store chunks with embeddings
            for chunk, embedding in zip(chunks, embeddings):
                chunk_record = ListingDocumentChunk(
                    listing_document_id=document_id,
                    content=chunk["content"],
                    embedding=embedding,
                    metadata=str(chunk["metadata"]),
                )
                db.add(chunk_record)

            await db.commit()

            return {
                "status": "success",
                "document_id": document_id,
                "chunks_created": len(chunks),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            await db.rollback()
            return {
                "status": "error",
                "message": str(e),
                "document_id": document_id,
            }
