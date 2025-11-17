"""Tests for agent service and tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.agent import AgentService, AgentTools


@pytest.mark.asyncio
async def test_identify_listing_by_code(db_session, test_broker, test_listing):
    """Test identifying listing by code."""
    tools = AgentTools(db_session)

    email_text = "Hi, I'm interested in listing TEST001. Can you tell me more?"
    result = await tools.identify_listing(email_text, str(test_broker.id))

    assert result["listing_id"] == str(test_listing.id)
    assert result["listing_code"] == "TEST001"
    assert result["confidence"] > 0.5


@pytest.mark.asyncio
async def test_identify_listing_by_title(db_session, test_broker, test_listing):
    """Test identifying listing by title keywords."""
    tools = AgentTools(db_session)

    email_text = "I saw your coffee shop listing. Is it still available?"
    result = await tools.identify_listing(email_text, str(test_broker.id))

    assert result["listing_id"] == str(test_listing.id)
    assert result["confidence"] > 0


@pytest.mark.asyncio
async def test_identify_listing_no_match(db_session, test_broker):
    """Test identifying listing with no match."""
    tools = AgentTools(db_session)

    email_text = "Do you have any restaurants?"
    result = await tools.identify_listing(email_text, str(test_broker.id))

    assert result["listing_id"] is None
    assert result["confidence"] == 0


@pytest.mark.asyncio
async def test_get_listing_summary(db_session, test_listing):
    """Test getting listing summary."""
    tools = AgentTools(db_session)

    result = await tools.get_listing_summary(str(test_listing.id))

    assert result["code"] == "TEST001"
    assert result["title"] == "Test Coffee Shop"
    assert result["asking_price"] == 500000
    assert result["location_region"] == "New York, NY"


@pytest.mark.asyncio
async def test_get_nda_status_none(db_session, test_lead, test_listing):
    """Test getting NDA status when no NDA exists."""
    tools = AgentTools(db_session)

    result = await tools.get_nda_status(str(test_lead.id), str(test_listing.id))

    assert result["status"] == "none"
    assert result["signed"] is False


@pytest.mark.asyncio
async def test_get_nda_status_signed(db_session, test_lead, test_listing):
    """Test getting NDA status when NDA is signed."""
    from app.models.lead import NDA, NDAStatus
    from datetime import datetime

    nda = NDA(
        lead_id=test_lead.id,
        listing_id=test_listing.id,
        status=NDAStatus.SIGNED,
        signed_at=datetime.utcnow(),
    )
    db_session.add(nda)
    await db_session.commit()

    tools = AgentTools(db_session)
    result = await tools.get_nda_status(str(test_lead.id), str(test_listing.id))

    assert result["status"] == "signed"
    assert result["signed"] is True


@pytest.mark.asyncio
async def test_generate_nda_link(db_session, test_broker, test_lead, test_listing):
    """Test generating NDA link."""
    tools = AgentTools(db_session)

    result = await tools.generate_nda_link(
        str(test_lead.id), str(test_listing.id), str(test_broker.id)
    )

    assert "https://example.com/nda" in result
    assert str(test_lead.id) in result
    assert str(test_listing.id) in result


@pytest.mark.asyncio
async def test_get_broker_settings(db_session, test_broker):
    """Test getting broker settings."""
    tools = AgentTools(db_session)

    result = await tools.get_broker_settings(str(test_broker.id))

    assert result["calendly_link"] == "https://calendly.com/test-broker"
    assert result["auto_send_enabled"] is False


@pytest.mark.asyncio
async def test_agent_generate_response(db_session, test_broker, mock_openai_service, mocker):
    """Test agent generating a response."""
    # Mock OpenAI service
    mocker.patch("app.services.agent.OpenAIService", return_value=mock_openai_service)

    agent = AgentService(db_session)

    conversation = [
        {"role": "user", "content": "Tell me about listing TEST001"}
    ]

    result = await agent.generate_response(
        conversation,
        str(test_broker.id),
    )

    assert "response_text" in result
    assert "tools_called" in result
    assert "confidence" in result
    assert "final_action" in result
    assert result["response_text"] == "This is a test response"


@pytest.mark.asyncio
async def test_agent_system_prompt():
    """Test agent system prompt contains key instructions."""
    agent = AgentService(None)
    prompt = agent.get_system_prompt()

    assert "business broker" in prompt.lower()
    assert "escalate" in prompt.lower()
    assert "nda" in prompt.lower()
    assert "never make up" in prompt.lower()


@pytest.mark.asyncio
async def test_agent_tool_definitions():
    """Test agent tool definitions are properly formatted."""
    agent = AgentService(None)
    tools = agent.create_tool_definitions()

    assert len(tools) >= 5
    tool_names = [t["function"]["name"] for t in tools]
    assert "identify_listing" in tool_names
    assert "get_listing_summary" in tool_names
    assert "get_nda_status" in tool_names
