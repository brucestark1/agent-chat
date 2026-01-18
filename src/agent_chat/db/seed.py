"""Seed data for development and testing."""

from agent_chat.db.connection import get_db
from agent_chat.db.models import Customer, Ticket


def seed_data() -> None:
    """Seed the database with sample customers and tickets."""
    with get_db() as db:
        # Check if data already exists
        if db.query(Customer).count() > 0:
            print("Database already seeded, skipping...")
            return

        # Create customers
        customers = [
            Customer(
                email="alice@example.com",
                name="Alice Johnson",
                plan="enterprise",
            ),
            Customer(
                email="bob@example.com",
                name="Bob Smith",
                plan="professional",
            ),
            Customer(
                email="carol@example.com",
                name="Carol Williams",
                plan="starter",
            ),
        ]
        db.add_all(customers)
        db.flush()  # Get IDs assigned

        # Create tickets
        tickets = [
            Ticket(
                customer_id=customers[0].id,
                subject="Cannot access API dashboard",
                description="Getting 403 errors when trying to access the API dashboard",
                status="open",
                priority="high",
            ),
            Ticket(
                customer_id=customers[0].id,
                subject="Rate limit increase request",
                description="Need to increase API rate limit for production deployment",
                status="in_progress",
                priority="medium",
            ),
            Ticket(
                customer_id=customers[1].id,
                subject="Billing question",
                description="Charged twice this month, need refund",
                status="open",
                priority="urgent",
            ),
            Ticket(
                customer_id=customers[2].id,
                subject="Documentation unclear",
                description="The authentication docs are confusing for OAuth flow",
                status="resolved",
                priority="low",
            ),
        ]
        db.add_all(tickets)
        db.commit()

        print(f"✓ Seeded {len(customers)} customers and {len(tickets)} tickets")


if __name__ == "__main__":
    from agent_chat.db.connection import init_db

    init_db()
    seed_data()
