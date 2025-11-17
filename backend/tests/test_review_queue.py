"""Tests for review queue endpoints."""

import pytest
from datetime import datetime
from httpx import AsyncClient

from app.models.agent import AgentRun, FinalAction
from app.models.email import EmailThread, EmailMessage, ThreadStatus, MessageDirection, MessageSentBy, AgentAction
from app.models.lead import Lead, LeadType
from app.models.listing import Listing, ListingStatus


@pytest.mark.asyncio
async def test_get_review_queue(
    client: AsyncClient,
    test_broker,
    auth_headers,
    db_session,
):
    """Test getting review queue."""
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

    # Create lead
    lead = Lead(
        broker_id=test_broker.id,
        email="lead@example.com",
        name="Test Lead",
        type=LeadType.BUYER,
    )
    db_session.add(lead)
    await db_session.flush()

    # Create thread that needs review
    thread = EmailThread(
        broker_id=test_broker.id,
        lead_id=lead.id,
        listing_id=listing.id,
        external_thread_id="ext123",
        status=ThreadStatus.NEEDS_BROKER,
        requires_review=True,
        priority_score=8.5,
    )
    db_session.add(thread)
    await db_session.flush()

    # Create inbound message
    inbound_msg = EmailMessage(
        email_thread_id=thread.id,
        direction=MessageDirection.INBOUND,
        from_email=lead.email,
        to_email=test_broker.email,
        subject="Inquiry about TEST001",
        body_text="What are the financial details?",
        sent_at=datetime.utcnow(),
        sent_by=MessageSentBy.LEAD,
    )
    db_session.add(inbound_msg)

    # Create agent run with escalation
    agent_run = AgentRun(
        email_thread_id=thread.id,
        llm_model="gpt-4",
        prompt="System prompt",
        response="I need to escalate this to the broker",
        confidence_score=0.35,
        final_action=FinalAction.ESCALATE,
        reasoning={
            "why_flagged": "Lead asked about proprietary financial details",
            "confidence": 0.35,
            "concerns": ["Potential confidentiality breach", "No NDA signed"],
            "confidence_factors": {
                "positive": [],
                "negative": [{"factor": "No NDA signed", "weight": -0.4}],
            },
        },
        tools_called=[{"name": "get_nda_status", "arguments": {}, "result": {"has_nda": False}}],
    )
    db_session.add(agent_run)
    await db_session.commit()

    # Test get review queue
    response = await client.get("/api/v1/review-queue", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    assert len(data["threads"]) == 1

    item = data["threads"][0]
    assert item["lead"]["name"] == "Test Lead"
    assert item["listing"]["code"] == "TEST001"
    assert item["status"] == "needs_broker"
    assert item["proposed_response"] == "I need to escalate this to the broker"
    assert item["priority_score"] == 8.5
    assert item["agent_reasoning"]["why_flagged"] == "Lead asked about proprietary financial details"
    assert item["agent_reasoning"]["confidence"] == 0.35
    assert "No NDA signed" in item["agent_reasoning"]["concerns"]
    assert "get_nda_status" in item["agent_reasoning"]["tools_called"]


@pytest.mark.asyncio
async def test_approve_email(
    client: AsyncClient,
    test_broker,
    auth_headers,
    db_session,
    mock_gmail_service,
):
    """Test approving and sending an email."""
    # Create lead
    lead = Lead(
        broker_id=test_broker.id,
        email="lead@example.com",
        name="Test Lead",
        type=LeadType.BUYER,
    )
    db_session.add(lead)
    await db_session.flush()

    # Create thread
    thread = EmailThread(
        broker_id=test_broker.id,
        lead_id=lead.id,
        external_thread_id="ext123",
        status=ThreadStatus.NEEDS_BROKER,
        requires_review=True,
        priority_score=8.5,
    )
    db_session.add(thread)
    await db_session.flush()

    # Create message
    message = EmailMessage(
        email_thread_id=thread.id,
        direction=MessageDirection.INBOUND,
        from_email=lead.email,
        to_email=test_broker.email,
        subject="Inquiry",
        body_text="Question",
        sent_at=datetime.utcnow(),
        sent_by=MessageSentBy.LEAD,
    )
    db_session.add(message)

    # Create agent run
    agent_run = AgentRun(
        email_thread_id=thread.id,
        llm_model="gpt-4",
        prompt="System prompt",
        response="Thank you for your inquiry",
        confidence_score=0.75,
        final_action=FinalAction.ANSWER,
    )
    db_session.add(agent_run)
    await db_session.commit()

    # Mock Gmail send_email
    mock_gmail_service.send_email.return_value = "msg_123"

    # Test approve without edits
    response = await client.post(
        f"/api/v1/review-queue/{thread.id}/approve",
        json={},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["sent_to"] == "lead@example.com"
    assert data["edited"] is False

    # Verify thread status updated
    await db_session.refresh(thread)
    assert thread.status == ThreadStatus.OPEN
    assert thread.requires_review is False


@pytest.mark.asyncio
async def test_approve_email_with_edits(
    client: AsyncClient,
    test_broker,
    auth_headers,
    db_session,
    mock_gmail_service,
):
    """Test approving email with edits."""
    # Create lead
    lead = Lead(
        broker_id=test_broker.id,
        email="lead@example.com",
        name="Test Lead",
        type=LeadType.BUYER,
    )
    db_session.add(lead)
    await db_session.flush()

    # Create thread
    thread = EmailThread(
        broker_id=test_broker.id,
        lead_id=lead.id,
        external_thread_id="ext123",
        status=ThreadStatus.NEEDS_BROKER,
        requires_review=True,
    )
    db_session.add(thread)
    await db_session.flush()

    # Create message
    message = EmailMessage(
        email_thread_id=thread.id,
        direction=MessageDirection.INBOUND,
        from_email=lead.email,
        to_email=test_broker.email,
        subject="Inquiry",
        body_text="Question",
        sent_at=datetime.utcnow(),
        sent_by=MessageSentBy.LEAD,
    )
    db_session.add(message)

    # Create agent run
    agent_run = AgentRun(
        email_thread_id=thread.id,
        llm_model="gpt-4",
        prompt="System prompt",
        response="Original response",
        confidence_score=0.75,
        final_action=FinalAction.ANSWER,
    )
    db_session.add(agent_run)
    await db_session.commit()

    # Mock Gmail
    mock_gmail_service.send_email.return_value = "msg_123"

    # Test approve with edits
    response = await client.post(
        f"/api/v1/review-queue/{thread.id}/approve",
        json={"edits": "Edited response text"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["edited"] is True

    # Verify Gmail was called with edited text
    mock_gmail_service.send_email.assert_called_once()
    call_args = mock_gmail_service.send_email.call_args
    assert call_args[1]["body"] == "Edited response text"


@pytest.mark.asyncio
async def test_send_manual_reply(
    client: AsyncClient,
    test_broker,
    auth_headers,
    db_session,
    mock_gmail_service,
):
    """Test sending manual reply."""
    # Create lead
    lead = Lead(
        broker_id=test_broker.id,
        email="lead@example.com",
        name="Test Lead",
        type=LeadType.BUYER,
    )
    db_session.add(lead)
    await db_session.flush()

    # Create thread
    thread = EmailThread(
        broker_id=test_broker.id,
        lead_id=lead.id,
        external_thread_id="ext123",
        status=ThreadStatus.NEEDS_BROKER,
        requires_review=True,
    )
    db_session.add(thread)
    await db_session.flush()

    # Create message
    message = EmailMessage(
        email_thread_id=thread.id,
        direction=MessageDirection.INBOUND,
        from_email=lead.email,
        to_email=test_broker.email,
        subject="Inquiry",
        body_text="Question",
        sent_at=datetime.utcnow(),
        sent_by=MessageSentBy.LEAD,
    )
    db_session.add(message)
    await db_session.commit()

    # Mock Gmail
    mock_gmail_service.send_email.return_value = "msg_123"

    # Test manual reply
    response = await client.post(
        f"/api/v1/review-queue/{thread.id}/manual-reply",
        json={"body_text": "This is my manual reply"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["sent_to"] == "lead@example.com"

    # Verify thread status updated
    await db_session.refresh(thread)
    assert thread.status == ThreadStatus.OPEN
    assert thread.requires_review is False

    # Verify Gmail was called
    mock_gmail_service.send_email.assert_called_once()
    call_args = mock_gmail_service.send_email.call_args
    assert call_args[1]["body"] == "This is my manual reply"


@pytest.mark.asyncio
async def test_mark_thread_resolved(
    client: AsyncClient,
    test_broker,
    auth_headers,
    db_session,
):
    """Test marking thread as resolved without sending."""
    # Create lead
    lead = Lead(
        broker_id=test_broker.id,
        email="lead@example.com",
        name="Test Lead",
        type=LeadType.BUYER,
    )
    db_session.add(lead)
    await db_session.flush()

    # Create thread
    thread = EmailThread(
        broker_id=test_broker.id,
        lead_id=lead.id,
        external_thread_id="ext123",
        status=ThreadStatus.NEEDS_BROKER,
        requires_review=True,
    )
    db_session.add(thread)
    await db_session.commit()

    # Test mark resolved
    response = await client.post(
        f"/api/v1/review-queue/{thread.id}/mark-resolved",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"

    # Verify thread status updated
    await db_session.refresh(thread)
    assert thread.status == ThreadStatus.CLOSED
    assert thread.requires_review is False


@pytest.mark.asyncio
async def test_review_queue_requires_auth(client: AsyncClient):
    """Test that review queue endpoints require authentication."""
    response = await client.get("/api/v1/review-queue")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_review_queue_thread_not_found(
    client: AsyncClient,
    test_broker,
    auth_headers,
):
    """Test 404 when thread doesn't exist."""
    from uuid import uuid4

    fake_thread_id = uuid4()

    response = await client.post(
        f"/api/v1/review-queue/{fake_thread_id}/approve",
        json={},
        headers=auth_headers,
    )

    assert response.status_code == 404
