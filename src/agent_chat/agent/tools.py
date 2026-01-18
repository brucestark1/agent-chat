"""Tool definitions for the agent to use.

These tools allow the agent to:
1. Query customer data
2. Query support tickets
3. Create new tickets
4. Update ticket status
"""

import time
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select

from agent_chat.agent.types import ToolResult
from agent_chat.db.connection import get_db
from agent_chat.db.models import Customer, Ticket


# Tool input schemas (used for validation)
class QueryCustomersInput(BaseModel):
    """Input schema for query_customers tool."""

    email: str | None = Field(None, description="Filter by customer email")
    plan: str | None = Field(None, description="Filter by plan (starter, professional, enterprise)")


class QueryTicketsInput(BaseModel):
    """Input schema for query_tickets tool."""

    customer_id: int | None = Field(None, description="Filter by customer ID")
    status: str | None = Field(
        None, description="Filter by status (open, in_progress, resolved, closed)"
    )
    priority: str | None = Field(None, description="Filter by priority (low, medium, high, urgent)")


class CreateTicketInput(BaseModel):
    """Input schema for create_ticket tool."""

    customer_id: int = Field(..., description="ID of the customer creating the ticket")
    subject: str = Field(..., description="Ticket subject/title")
    description: str = Field(..., description="Detailed description of the issue")
    priority: str = Field("medium", description="Priority: low, medium, high, or urgent")


class UpdateTicketInput(BaseModel):
    """Input schema for update_ticket tool."""

    ticket_id: int = Field(..., description="ID of the ticket to update")
    status: str = Field(..., description="New status: open, in_progress, resolved, or closed")


# Tool functions
def query_customers(email: str | None = None, plan: str | None = None) -> ToolResult:
    """Query customers from the database.

    Args:
        email: Optional email filter
        plan: Optional plan filter (starter, professional, enterprise)

    Returns:
        ToolResult with list of matching customers
    """
    try:
        with get_db() as db:
            query = select(Customer)
            if email:
                query = query.where(Customer.email.ilike(f"%{email}%"))
            if plan:
                query = query.where(Customer.plan == plan)

            customers = db.execute(query).scalars().all()

            data = [
                {
                    "id": c.id,
                    "email": c.email,
                    "name": c.name,
                    "plan": c.plan,
                    "created_at": c.created_at.isoformat(),
                }
                for c in customers
            ]

            return ToolResult(success=True, data=data)
    except Exception as e:
        return ToolResult(success=False, error=str(e))


def query_tickets(
    customer_id: int | None = None,
    status: str | None = None,
    priority: str | None = None,
) -> ToolResult:
    """Query support tickets from the database.

    Args:
        customer_id: Optional customer ID filter
        status: Optional status filter (open, in_progress, resolved, closed)
        priority: Optional priority filter (low, medium, high, urgent)

    Returns:
        ToolResult with list of matching tickets
    """
    try:
        with get_db() as db:
            query = select(Ticket)
            if customer_id:
                query = query.where(Ticket.customer_id == customer_id)
            if status:
                query = query.where(Ticket.status == status)
            if priority:
                query = query.where(Ticket.priority == priority)

            tickets = db.execute(query).scalars().all()

            data = [
                {
                    "id": t.id,
                    "customer_id": t.customer_id,
                    "subject": t.subject,
                    "description": t.description,
                    "status": t.status,
                    "priority": t.priority,
                    "created_at": t.created_at.isoformat(),
                    "updated_at": t.updated_at.isoformat(),
                }
                for t in tickets
            ]

            return ToolResult(success=True, data=data)
    except Exception as e:
        return ToolResult(success=False, error=str(e))


def create_ticket(
    customer_id: int, subject: str, description: str, priority: str = "medium"
) -> ToolResult:
    """Create a new support ticket.

    Args:
        customer_id: ID of the customer
        subject: Ticket subject
        description: Detailed description
        priority: Priority level (default: medium)

    Returns:
        ToolResult with the created ticket data
    """
    try:
        with get_db() as db:
            # Verify customer exists
            customer = db.get(Customer, customer_id)
            if not customer:
                return ToolResult(success=False, error=f"Customer {customer_id} not found")

            ticket = Ticket(
                customer_id=customer_id,
                subject=subject,
                description=description,
                status="open",
                priority=priority,
            )
            db.add(ticket)
            db.commit()
            db.refresh(ticket)

            data = {
                "id": ticket.id,
                "customer_id": ticket.customer_id,
                "subject": ticket.subject,
                "description": ticket.description,
                "status": ticket.status,
                "priority": ticket.priority,
                "created_at": ticket.created_at.isoformat(),
            }

            return ToolResult(success=True, data=data)
    except Exception as e:
        return ToolResult(success=False, error=str(e))


def update_ticket(ticket_id: int, status: str) -> ToolResult:
    """Update a ticket's status.

    Args:
        ticket_id: ID of the ticket to update
        status: New status (open, in_progress, resolved, closed)

    Returns:
        ToolResult with the updated ticket data
    """
    valid_statuses = ["open", "in_progress", "resolved", "closed"]
    if status not in valid_statuses:
        return ToolResult(success=False, error=f"Invalid status. Must be one of: {valid_statuses}")

    try:
        with get_db() as db:
            ticket = db.get(Ticket, ticket_id)
            if not ticket:
                return ToolResult(success=False, error=f"Ticket {ticket_id} not found")

            ticket.status = status
            db.commit()
            db.refresh(ticket)

            data = {
                "id": ticket.id,
                "customer_id": ticket.customer_id,
                "subject": ticket.subject,
                "status": ticket.status,
                "priority": ticket.priority,
                "updated_at": ticket.updated_at.isoformat(),
            }

            return ToolResult(success=True, data=data)
    except Exception as e:
        return ToolResult(success=False, error=str(e))


# Tool registry - maps tool names to their functions and schemas
TOOLS = {
    "query_customers": {
        "function": query_customers,
        "schema": QueryCustomersInput,
        "description": "Query customer data by email or plan type",
    },
    "query_tickets": {
        "function": query_tickets,
        "schema": QueryTicketsInput,
        "description": "Query support tickets by customer, status, or priority",
    },
    "create_ticket": {
        "function": create_ticket,
        "schema": CreateTicketInput,
        "description": "Create a new support ticket for a customer",
    },
    "update_ticket": {
        "function": update_ticket,
        "schema": UpdateTicketInput,
        "description": "Update the status of an existing ticket",
    },
}


def execute_tool(tool_name: str, tool_input: dict[str, Any]) -> tuple[ToolResult, int]:
    """Execute a tool by name with input validation.

    Args:
        tool_name: Name of the tool to execute
        tool_input: Input parameters as dictionary

    Returns:
        Tuple of (ToolResult, latency_ms)
    """
    if tool_name not in TOOLS:
        return ToolResult(success=False, error=f"Unknown tool: {tool_name}"), 0

    tool_config = TOOLS[tool_name]

    # Validate input
    try:
        validated_input = tool_config["schema"](**tool_input)
    except Exception as e:
        return ToolResult(success=False, error=f"Invalid input: {e}"), 0

    # Execute tool
    start_time = time.time()
    try:
        result = tool_config["function"](**validated_input.model_dump())
        latency_ms = int((time.time() - start_time) * 1000)
        return result, latency_ms
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return ToolResult(success=False, error=f"Tool execution error: {e}"), latency_ms


def get_tool_definitions() -> list[dict[str, Any]]:
    """Get tool definitions in Anthropic format for the API.

    Returns:
        List of tool definitions that can be passed to Claude
    """
    definitions = []
    for name, config in TOOLS.items():
        schema = config["schema"]
        definitions.append(
            {
                "name": name,
                "description": config["description"],
                "input_schema": schema.model_json_schema(),
            }
        )
    return definitions
