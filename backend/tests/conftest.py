"""Pytest configuration and fixtures."""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.database import Base
from app.core.config import settings
from app.models import *  # noqa: F401, F403


# Test database URL (use in-memory SQLite for speed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_broker(db_session: AsyncSession):
    """Create a test broker."""
    from app.models.broker import Broker, BrokerSettings
    from app.core.security import get_password_hash

    broker = Broker(
        name="Test Broker",
        email="test@example.com",
        password_hash=get_password_hash("testpass123"),
        timezone="America/New_York",
    )
    db_session.add(broker)
    await db_session.flush()

    settings = BrokerSettings(
        broker_id=broker.id,
        auto_send_enabled=False,
        batch_windows=[
            {"start": "09:00", "end": "09:30"},
            {"start": "14:00", "end": "14:30"},
        ],
        calendly_link="https://calendly.com/test-broker",
        default_nda_url="https://example.com/nda",
    )
    db_session.add(settings)
    await db_session.commit()
    await db_session.refresh(broker)

    return broker


@pytest_asyncio.fixture
async def test_listing(db_session: AsyncSession, test_broker):
    """Create a test listing."""
    from app.models.listing import Listing, ListingStatus, ConfidentialityLevel

    listing = Listing(
        broker_id=test_broker.id,
        code="TEST001",
        title="Test Coffee Shop",
        status=ListingStatus.ACTIVE,
        asking_price=500000,
        revenue=750000,
        sde=150000,
        location_region="New York, NY",
        confidentiality_level=ConfidentialityLevel.HIGH,
        short_description="A great coffee shop in Manhattan",
    )
    db_session.add(listing)
    await db_session.commit()
    await db_session.refresh(listing)

    return listing


@pytest_asyncio.fixture
async def test_lead(db_session: AsyncSession, test_broker):
    """Create a test lead."""
    from app.models.lead import Lead, LeadType

    lead = Lead(
        broker_id=test_broker.id,
        email="buyer@example.com",
        name="Test Buyer",
        type=LeadType.BUYER,
    )
    db_session.add(lead)
    await db_session.commit()
    await db_session.refresh(lead)

    return lead


@pytest_asyncio.fixture
async def test_email_thread(db_session: AsyncSession, test_broker, test_lead, test_listing):
    """Create a test email thread."""
    from app.models.email import EmailThread, ThreadStatus, AgentAction

    thread = EmailThread(
        broker_id=test_broker.id,
        lead_id=test_lead.id,
        listing_id=test_listing.id,
        external_thread_id="thread_123",
        status=ThreadStatus.OPEN,
        last_agent_action=AgentAction.NONE,
    )
    db_session.add(thread)
    await db_session.commit()
    await db_session.refresh(thread)

    return thread


@pytest.fixture
def mock_gmail_service(mocker):
    """Mock Gmail service."""
    mock = mocker.MagicMock()
    mock.get_unprocessed_messages.return_value = []
    mock.get_message.return_value = {
        "id": "msg_123",
        "threadId": "thread_123",
        "payload": {
            "headers": [
                {"name": "From", "value": "buyer@example.com"},
                {"name": "To", "value": "broker@example.com"},
                {"name": "Subject", "value": "Interested in TEST001"},
            ],
            "body": {"data": "SSdtIGludGVyZXN0ZWQgaW4gdGhpcyBsaXN0aW5n"},
        },
    }
    mock.send_email.return_value = "msg_456"
    return mock


@pytest.fixture
def mock_s3_service(mocker):
    """Mock S3 service."""
    mock = mocker.MagicMock()
    mock.upload_file.return_value = True
    mock.download_file.return_value = b"test file content"
    mock.get_signed_url.return_value = "https://s3.example.com/signed-url"
    mock.file_exists.return_value = True
    return mock


@pytest.fixture
def mock_openai_service(mocker):
    """Mock OpenAI service."""
    mock = mocker.MagicMock()
    mock.chat_completion.return_value = {
        "content": "This is a test response",
        "tool_calls": None,
        "finish_reason": "stop",
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        },
    }
    mock.create_embedding.return_value = [0.1] * 1536
    mock.create_embeddings_batch.return_value = [[0.1] * 1536]
    return mock
