"""Tests for analytics endpoints."""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient

from app.models.agent import AgentRun, FinalAction
from app.models.email import EmailThread, EmailMessage, ThreadStatus, MessageDirection, MessageSentBy, AgentAction
from app.models.listing import Listing, ListingStatus


@pytest.mark.asyncio
async def test_get_analytics_overview(
    client: AsyncClient,
    test_broker,
    auth_headers,
    db_session,
):
    """Test analytics overview endpoint."""
    # Create a listing
    listing = Listing(
        broker_id=test_broker.id,
        code="TEST001",
        title="Test Business",
        asking_price=500000,
        revenue=750000,
        sde=150000,
        location_region="New York, NY",
        short_description="Test",
        status=ListingStatus.ACTIVE,
    )
    db_session.add(listing)

    # Create test lead
    from app.models.lead import Lead, LeadType

    lead = Lead(
        broker_id=test_broker.id,
        email="lead@example.com",
        name="Test Lead",
        type=LeadType.BUYER,
    )
    db_session.add(lead)
    await db_session.flush()

    # Create email thread
    thread = EmailThread(
        broker_id=test_broker.id,
        lead_id=lead.id,
        listing_id=listing.id,
        external_thread_id="ext123",
        status=ThreadStatus.OPEN,
    )
    db_session.add(thread)
    await db_session.flush()

    # Create agent runs with different actions
    agent_runs = [
        AgentRun(
            email_thread_id=thread.id,
            llm_model="gpt-4",
            prompt="System prompt",
            response="Answer to inquiry",
            confidence_score=0.85,
            final_action=FinalAction.ANSWER,
        ),
        AgentRun(
            email_thread_id=thread.id,
            llm_model="gpt-4",
            prompt="System prompt",
            response="Escalating to broker",
            confidence_score=0.35,
            final_action=FinalAction.ESCALATE,
        ),
        AgentRun(
            email_thread_id=thread.id,
            llm_model="gpt-4",
            prompt="System prompt",
            response="Please sign NDA",
            confidence_score=0.80,
            final_action=FinalAction.ASK_NDA,
        ),
    ]

    for run in agent_runs:
        db_session.add(run)

    await db_session.commit()

    # Test overview endpoint
    response = await client.get("/api/v1/analytics/overview?period=7d", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["period"] == "7d"
    assert data["total_emails"] == 3
    assert data["auto_reply_rate"] == pytest.approx(1 / 3, rel=0.01)  # 1 answer out of 3
    assert data["escalation_rate"] == pytest.approx(1 / 3, rel=0.01)  # 1 escalation out of 3
    assert data["nda_request_rate"] == pytest.approx(1 / 3, rel=0.01)  # 1 NDA request out of 3
    assert data["avg_confidence"] > 0.6  # Average of 0.85, 0.35, 0.80


@pytest.mark.asyncio
async def test_get_email_activity(
    client: AsyncClient,
    test_broker,
    auth_headers,
    db_session,
):
    """Test email activity log endpoint."""
    # Create test data
    from app.models.lead import Lead, LeadType

    lead = Lead(
        broker_id=test_broker.id,
        email="lead@example.com",
        name="Test Lead",
        type=LeadType.BUYER,
    )
    db_session.add(lead)
    await db_session.flush()

    thread = EmailThread(
        broker_id=test_broker.id,
        lead_id=lead.id,
        external_thread_id="ext123",
        status=ThreadStatus.OPEN,
    )
    db_session.add(thread)
    await db_session.flush()

    # Create outbound message (sent by agent)
    message = EmailMessage(
        email_thread_id=thread.id,
        direction=MessageDirection.OUTBOUND,
        from_email=test_broker.email,
        to_email=lead.email,
        subject="Re: Inquiry",
        body_text="Thank you for your inquiry",
        sent_at=datetime.utcnow(),
        sent_by=MessageSentBy.AGENT,
    )
    db_session.add(message)

    # Create agent run
    agent_run = AgentRun(
        email_thread_id=thread.id,
        llm_model="gpt-4",
        prompt="System prompt",
        response="Thank you for your inquiry",
        confidence_score=0.85,
        final_action=FinalAction.ANSWER,
        tools_called=[{"name": "identify_listing", "arguments": {}, "result": {}}],
    )
    db_session.add(agent_run)
    await db_session.commit()

    # Test activity endpoint
    response = await client.get("/api/v1/analytics/emails", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    assert len(data["emails"]) == 1

    email = data["emails"][0]
    assert email["lead_name"] == "Test Lead"
    assert email["lead_email"] == "lead@example.com"
    assert email["status"] == "sent"
    assert email["sent_by"] == "agent"
    assert email["confidence"] == 0.85
    assert email["final_action"] == "answer"
    assert "identify_listing" in email["tools_called"]


@pytest.mark.asyncio
async def test_get_analytics_trends(
    client: AsyncClient,
    test_broker,
    auth_headers,
    db_session,
):
    """Test analytics trends endpoint."""
    # Create listing
    listing = Listing(
        broker_id=test_broker.id,
        code="TEST001",
        title="Test Business",
        asking_price=500000,
        revenue=750000,
        sde=150000,
        location_region="New York, NY",
        short_description="Test",
        status=ListingStatus.ACTIVE,
    )
    db_session.add(listing)

    # Create test lead
    from app.models.lead import Lead, LeadType

    lead = Lead(
        broker_id=test_broker.id,
        email="lead@example.com",
        name="Test Lead",
        type=LeadType.BUYER,
    )
    db_session.add(lead)
    await db_session.flush()

    # Create threads and agent runs
    for i in range(5):
        thread = EmailThread(
            broker_id=test_broker.id,
            lead_id=lead.id,
            listing_id=listing.id,
            external_thread_id=f"ext{i}",
            status=ThreadStatus.OPEN,
        )
        db_session.add(thread)
        await db_session.flush()

        agent_run = AgentRun(
            email_thread_id=thread.id,
            llm_model="gpt-4",
            prompt="System prompt",
            response="Response",
            confidence_score=0.85,
            final_action=FinalAction.ANSWER,
            created_at=datetime.utcnow() - timedelta(days=i),
        )
        db_session.add(agent_run)

    await db_session.commit()

    # Test trends endpoint
    response = await client.get("/api/v1/analytics/trends?period=7d", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert len(data["daily_counts"]) > 0
    assert len(data["by_listing"]) == 1
    assert data["by_listing"][0]["listing_code"] == "TEST001"
    assert data["by_listing"][0]["count"] == 5
    assert data["by_action"]["answered"] == 5
    assert data["by_action"]["escalated"] == 0


@pytest.mark.asyncio
async def test_analytics_with_date_filter(
    client: AsyncClient,
    test_broker,
    auth_headers,
    db_session,
):
    """Test analytics with date filtering."""
    from app.models.lead import Lead, LeadType

    lead = Lead(
        broker_id=test_broker.id,
        email="lead@example.com",
        name="Test Lead",
        type=LeadType.BUYER,
    )
    db_session.add(lead)
    await db_session.flush()

    thread = EmailThread(
        broker_id=test_broker.id,
        lead_id=lead.id,
        external_thread_id="ext123",
        status=ThreadStatus.OPEN,
    )
    db_session.add(thread)
    await db_session.flush()

    # Create old agent run (outside filter range)
    old_run = AgentRun(
        email_thread_id=thread.id,
        llm_model="gpt-4",
        prompt="System prompt",
        response="Old response",
        confidence_score=0.85,
        final_action=FinalAction.ANSWER,
        created_at=datetime.utcnow() - timedelta(days=100),
    )
    db_session.add(old_run)

    # Create recent agent run
    recent_run = AgentRun(
        email_thread_id=thread.id,
        llm_model="gpt-4",
        prompt="System prompt",
        response="Recent response",
        confidence_score=0.85,
        final_action=FinalAction.ANSWER,
        created_at=datetime.utcnow(),
    )
    db_session.add(recent_run)
    await db_session.commit()

    # Test with 7d filter
    response = await client.get("/api/v1/analytics/overview?period=7d", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Should only include recent run
    assert data["total_emails"] == 1

    # Test with 'all' filter
    response = await client.get("/api/v1/analytics/overview?period=all", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Should include both runs
    assert data["total_emails"] == 2
