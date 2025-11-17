"""Analytics endpoints."""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_current_broker
from app.core.database import get_db
from app.models.broker import Broker
from app.models.email import EmailThread, EmailMessage, MessageDirection, MessageSentBy
from app.models.agent import AgentRun, FinalAction
from app.models.lead import Lead
from app.models.listing import Listing
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    EmailActivityResponse,
    EmailActivityItem,
    AnalyticsTrendsResponse,
    DailyCount,
    ListingCount,
    ActionBreakdown,
)

router = APIRouter()


def _get_period_start(period: str) -> Optional[datetime]:
    """Get start datetime for period."""
    now = datetime.utcnow()

    if period == "7d":
        return now - timedelta(days=7)
    elif period == "30d":
        return now - timedelta(days=30)
    elif period == "90d":
        return now - timedelta(days=90)
    elif period == "all":
        return None
    else:
        return now - timedelta(days=7)  # Default to 7 days


@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def get_analytics_overview(
    period: str = Query("7d", regex="^(7d|30d|90d|all)$"),
    current_broker: Broker = Depends(get_current_broker),
    db: AsyncSession = Depends(get_db),
):
    """
    Get analytics overview with KPIs.

    Args:
        period: Time period (7d, 30d, 90d, all)
        current_broker: Authenticated broker
        db: Database session

    Returns:
        Overview analytics with KPIs
    """
    start_date = _get_period_start(period)

    # Build base query for agent runs in period
    query = (
        select(AgentRun)
        .join(EmailThread, AgentRun.email_thread_id == EmailThread.id)
        .where(EmailThread.broker_id == current_broker.id)
    )

    if start_date:
        query = query.where(AgentRun.created_at >= start_date)

    result = await db.execute(query)
    agent_runs = result.scalars().all()

    if not agent_runs:
        return AnalyticsOverviewResponse(
            period=period,
            total_emails=0,
            auto_reply_rate=0.0,
            escalation_rate=0.0,
            avg_confidence=0.0,
            nda_request_rate=0.0,
        )

    total_emails = len(agent_runs)

    # Calculate metrics
    auto_replies = sum(1 for run in agent_runs if run.final_action == FinalAction.ANSWER)
    escalations = sum(1 for run in agent_runs if run.final_action == FinalAction.ESCALATE)
    nda_requests = sum(1 for run in agent_runs if run.final_action == FinalAction.ASK_NDA)

    confidences = [float(run.confidence_score) for run in agent_runs if run.confidence_score is not None]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    return AnalyticsOverviewResponse(
        period=period,
        total_emails=total_emails,
        auto_reply_rate=auto_replies / total_emails if total_emails > 0 else 0.0,
        escalation_rate=escalations / total_emails if total_emails > 0 else 0.0,
        avg_confidence=avg_confidence,
        nda_request_rate=nda_requests / total_emails if total_emails > 0 else 0.0,
    )


@router.get("/emails", response_model=EmailActivityResponse)
async def get_email_activity(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    listing_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_broker: Broker = Depends(get_current_broker),
    db: AsyncSession = Depends(get_db),
):
    """
    Get paginated email activity log.

    Args:
        start_date: Filter by start date
        end_date: Filter by end date
        listing_id: Filter by listing
        status: Filter by status (sent/draft)
        skip: Pagination offset
        limit: Pagination limit
        current_broker: Authenticated broker
        db: Database session

    Returns:
        Paginated email activity records
    """
    # Query outbound messages with agent runs
    query = (
        select(EmailMessage, AgentRun, Lead, Listing)
        .join(EmailThread, EmailMessage.email_thread_id == EmailThread.id)
        .outerjoin(AgentRun, AgentRun.email_thread_id == EmailThread.id)
        .join(Lead, EmailThread.lead_id == Lead.id)
        .outerjoin(Listing, EmailThread.listing_id == Listing.id)
        .where(
            and_(
                EmailThread.broker_id == current_broker.id,
                EmailMessage.direction == MessageDirection.OUTBOUND,
            )
        )
    )

    # Apply filters
    if start_date:
        query = query.where(EmailMessage.sent_at >= start_date)
    if end_date:
        query = query.where(EmailMessage.sent_at <= end_date)
    if listing_id:
        query = query.where(EmailThread.listing_id == listing_id)
    if status == "sent":
        query = query.where(EmailMessage.sent_by.in_([MessageSentBy.AGENT, MessageSentBy.BROKER]))
    elif status == "draft":
        # Drafts are agent runs without corresponding sent messages
        # This is simplified - in reality need more complex logic
        pass

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination and ordering
    query = query.order_by(EmailMessage.sent_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    # Build response items
    emails = []
    for message, agent_run, lead, listing in rows:
        # Determine status
        msg_status = "sent" if message.sent_by in [MessageSentBy.AGENT, MessageSentBy.BROKER] else "draft"

        # Extract tools called
        tools_called = None
        if agent_run and agent_run.tools_called:
            if isinstance(agent_run.tools_called, list):
                tools_called = [
                    tool["name"] if isinstance(tool, dict) else str(tool)
                    for tool in agent_run.tools_called
                ]

        emails.append(
            EmailActivityItem(
                id=message.id,
                thread_id=message.email_thread_id,
                lead_name=lead.name,
                lead_email=lead.email,
                listing_code=listing.code if listing else None,
                listing_title=listing.title if listing else None,
                subject=message.subject or "",
                sent_at=message.sent_at,
                status=msg_status,
                sent_by=message.sent_by.value,
                confidence=float(agent_run.confidence_score) if agent_run and agent_run.confidence_score else None,
                final_action=agent_run.final_action.value if agent_run else None,
                tools_called=tools_called,
            )
        )

    return EmailActivityResponse(
        emails=emails,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/trends", response_model=AnalyticsTrendsResponse)
async def get_analytics_trends(
    period: str = Query("30d", regex="^(7d|30d|90d|all)$"),
    current_broker: Broker = Depends(get_current_broker),
    db: AsyncSession = Depends(get_db),
):
    """
    Get analytics trends and breakdowns.

    Args:
        period: Time period (7d, 30d, 90d, all)
        current_broker: Authenticated broker
        db: Database session

    Returns:
        Trends data (daily counts, by listing, by action)
    """
    start_date = _get_period_start(period)

    # Base query for agent runs
    base_query = (
        select(AgentRun)
        .join(EmailThread, AgentRun.email_thread_id == EmailThread.id)
        .where(EmailThread.broker_id == current_broker.id)
    )

    if start_date:
        base_query = base_query.where(AgentRun.created_at >= start_date)

    result = await db.execute(base_query)
    agent_runs = result.scalars().all()

    # 1. Daily counts
    daily_map = {}
    for run in agent_runs:
        date_str = run.created_at.date().isoformat()
        daily_map[date_str] = daily_map.get(date_str, 0) + 1

    daily_counts = [
        DailyCount(date=date, count=count)
        for date, count in sorted(daily_map.items())
    ]

    # 2. By listing
    # Need to join with threads to get listing_id
    listing_query = (
        select(Listing.code, Listing.title, func.count(AgentRun.id).label("count"))
        .join(EmailThread, AgentRun.email_thread_id == EmailThread.id)
        .join(Listing, EmailThread.listing_id == Listing.id)
        .where(EmailThread.broker_id == current_broker.id)
    )

    if start_date:
        listing_query = listing_query.where(AgentRun.created_at >= start_date)

    listing_query = (
        listing_query.group_by(Listing.code, Listing.title)
        .order_by(func.count(AgentRun.id).desc())
        .limit(10)
    )

    listing_result = await db.execute(listing_query)
    listing_rows = listing_result.all()

    by_listing = [
        ListingCount(listing_code=code, listing_title=title, count=count)
        for code, title, count in listing_rows
    ]

    # 3. By action
    action_counts = {
        "answered": 0,
        "escalated": 0,
        "nda_requested": 0,
        "meeting_booked": 0,
    }

    for run in agent_runs:
        if run.final_action == FinalAction.ANSWER:
            action_counts["answered"] += 1
        elif run.final_action == FinalAction.ESCALATE:
            action_counts["escalated"] += 1
        elif run.final_action == FinalAction.ASK_NDA:
            action_counts["nda_requested"] += 1
        elif run.final_action == FinalAction.BOOK_MEETING:
            action_counts["meeting_booked"] += 1

    by_action = ActionBreakdown(**action_counts)

    return AnalyticsTrendsResponse(
        daily_counts=daily_counts,
        by_listing=by_listing,
        by_action=by_action,
    )
