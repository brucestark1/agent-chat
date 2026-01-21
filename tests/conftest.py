"""Pytest configuration and fixtures."""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from agent_chat.db.models import Base, Customer, Ticket


@pytest.fixture
def test_db() -> Generator[Session]:
    """Create a clean in-memory database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    # Add test data
    customers = [
        Customer(id=1, email="test@example.com", name="Test User", plan="professional"),
        Customer(id=2, email="admin@example.com", name="Admin User", plan="enterprise"),
    ]
    db.add_all(customers)

    tickets = [
        Ticket(
            id=1,
            customer_id=1,
            subject="Test ticket",
            description="This is a test",
            status="open",
            priority="medium",
        ),
        Ticket(
            id=2,
            customer_id=2,
            subject="Urgent issue",
            description="Need help ASAP",
            status="open",
            priority="urgent",
        ),
    ]
    db.add_all(tickets)
    db.commit()

    yield db

    db.close()
