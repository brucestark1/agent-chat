"""SQLAlchemy ORM models for persistence."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, ForeignKey, String, Text, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class Thread(Base):
    """Conversation thread containing multiple messages."""

    __tablename__ = "threads"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("CURRENT_TIMESTAMP"), onupdate=datetime.utcnow
    )

    # Relationships
    messages: Mapped[list["Message"]] = relationship(
        back_populates="thread", cascade="all, delete-orphan"
    )
    runs: Mapped[list["Run"]] = relationship(back_populates="thread", cascade="all, delete-orphan")


class Message(Base):
    """Individual message in a conversation."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("threads.id"))
    role: Mapped[str] = mapped_column(String(20))  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))

    # Relationships
    thread: Mapped["Thread"] = relationship(back_populates="messages")


class Run(Base):
    """A single execution of the agent loop (one POST /chat call)."""

    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("threads.id"))
    user_message: Mapped[str] = mapped_column(Text)
    assistant_message: Mapped[str] = mapped_column(Text)
    iterations: Mapped[int]  # Number of agent loop iterations
    status: Mapped[str] = mapped_column(String(20))  # 'success', 'error', 'max_iterations'
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    thread: Mapped["Thread"] = relationship(back_populates="runs")
    tool_calls: Mapped[list["ToolCall"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class ToolCall(Base):
    """Record of a single tool execution within a run."""

    __tablename__ = "tool_calls"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"))
    tool_name: Mapped[str] = mapped_column(String(100))
    tool_input: Mapped[dict[str, Any]] = mapped_column(JSON)
    tool_output: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))

    # Relationships
    run: Mapped["Run"] = relationship(back_populates="tool_calls")


# Seed data tables (simple key-value stores)
class Customer(Base):
    """Customer data for agent tools to query."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    plan: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))


class Ticket(Base):
    """Support ticket data for agent tools to query and update."""

    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    subject: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50))  # 'open', 'in_progress', 'resolved', 'closed'
    priority: Mapped[str] = mapped_column(String(20))  # 'low', 'medium', 'high', 'urgent'
    created_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("CURRENT_TIMESTAMP"), onupdate=datetime.utcnow
    )

    # Relationships
    customer: Mapped["Customer"] = relationship()
