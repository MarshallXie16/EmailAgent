"""Initialize database with pgvector extension and create initial broker."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import engine, AsyncSessionLocal, Base
from app.models import *  # noqa: F401, F403
from app.models.broker import Broker, BrokerSettings
from app.core.security import get_password_hash


async def init_database():
    """Initialize database schema and pgvector extension."""
    print("Initializing database...")

    # Create pgvector extension
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        print("✓ pgvector extension created")

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✓ Database tables created")

    print("Database initialization complete!")


async def create_initial_broker(
    name: str = "Demo Broker",
    email: str = "broker@example.com",
    password: str = "password123",
):
    """Create an initial broker for testing."""
    print(f"\nCreating initial broker: {email}")

    async with AsyncSessionLocal() as session:
        # Check if broker already exists
        from sqlalchemy import select

        result = await session.execute(select(Broker).where(Broker.email == email))
        existing = result.scalar_one_or_none()

        if existing:
            print(f"⚠ Broker {email} already exists")
            return

        # Create broker
        broker = Broker(
            name=name,
            email=email,
            password_hash=get_password_hash(password),
            timezone="America/New_York",
        )
        session.add(broker)
        await session.flush()

        # Create default settings
        settings = BrokerSettings(
            broker_id=broker.id,
            auto_send_enabled=False,
            batch_windows=[
                {"start": "09:00", "end": "09:30"},
                {"start": "12:00", "end": "12:30"},
                {"start": "16:00", "end": "16:30"},
            ],
        )
        session.add(settings)

        await session.commit()

        print(f"✓ Broker created successfully")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
        print(f"  ID: {broker.id}")


async def main():
    """Main function."""
    print("=" * 50)
    print("Email Agent - Database Initialization")
    print("=" * 50)

    # Initialize database
    await init_database()

    # Create initial broker
    await create_initial_broker()

    print("\n" + "=" * 50)
    print("Setup complete! You can now:")
    print("1. Start the backend: uvicorn app.main:app --reload")
    print("2. Login with broker@example.com / password123")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
