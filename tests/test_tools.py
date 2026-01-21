"""Unit tests for tool execution."""

from unittest.mock import patch

from agent_chat.agent.tools import (
    create_ticket,
    execute_tool,
    get_tool_definitions,
    query_customers,
    query_tickets,
    update_ticket,
)


def test_query_customers_all(test_db):  # type: ignore
    """Test querying all customers."""
    with patch("agent_chat.agent.tools.get_db") as mock_get_db:
        mock_get_db.return_value.__enter__.return_value = test_db

        result = query_customers()

        assert result.success is True
        assert len(result.data) == 2
        assert result.data[0]["email"] == "test@example.com"


def test_query_customers_by_email(test_db):  # type: ignore
    """Test querying customers by email filter."""
    with patch("agent_chat.agent.tools.get_db") as mock_get_db:
        mock_get_db.return_value.__enter__.return_value = test_db

        result = query_customers(email="admin")

        assert result.success is True
        assert len(result.data) == 1
        assert result.data[0]["email"] == "admin@example.com"


def test_query_customers_by_plan(test_db):  # type: ignore
    """Test querying customers by plan filter."""
    with patch("agent_chat.agent.tools.get_db") as mock_get_db:
        mock_get_db.return_value.__enter__.return_value = test_db

        result = query_customers(plan="enterprise")

        assert result.success is True
        assert len(result.data) == 1
        assert result.data[0]["plan"] == "enterprise"


def test_query_tickets_all(test_db):  # type: ignore
    """Test querying all tickets."""
    with patch("agent_chat.agent.tools.get_db") as mock_get_db:
        mock_get_db.return_value.__enter__.return_value = test_db

        result = query_tickets()

        assert result.success is True
        assert len(result.data) == 2


def test_query_tickets_by_status(test_db):  # type: ignore
    """Test querying tickets by status."""
    with patch("agent_chat.agent.tools.get_db") as mock_get_db:
        mock_get_db.return_value.__enter__.return_value = test_db

        result = query_tickets(status="open")

        assert result.success is True
        assert len(result.data) == 2
        assert all(t["status"] == "open" for t in result.data)


def test_query_tickets_by_priority(test_db):  # type: ignore
    """Test querying tickets by priority."""
    with patch("agent_chat.agent.tools.get_db") as mock_get_db:
        mock_get_db.return_value.__enter__.return_value = test_db

        result = query_tickets(priority="urgent")

        assert result.success is True
        assert len(result.data) == 1
        assert result.data[0]["priority"] == "urgent"


def test_create_ticket(test_db):  # type: ignore
    """Test creating a new ticket."""
    with patch("agent_chat.agent.tools.get_db") as mock_get_db:
        mock_get_db.return_value.__enter__.return_value = test_db

        result = create_ticket(
            customer_id=1, subject="New issue", description="Need help", priority="high"
        )

        assert result.success is True
        assert result.data["subject"] == "New issue"
        assert result.data["status"] == "open"
        assert result.data["priority"] == "high"


def test_create_ticket_invalid_customer(test_db):  # type: ignore
    """Test creating a ticket for non-existent customer."""
    with patch("agent_chat.agent.tools.get_db") as mock_get_db:
        mock_get_db.return_value.__enter__.return_value = test_db

        result = create_ticket(
            customer_id=999, subject="New issue", description="Need help", priority="high"
        )

        assert result.success is False
        assert result.error is not None
        assert "not found" in result.error


def test_update_ticket(test_db):  # type: ignore
    """Test updating a ticket status."""
    with patch("agent_chat.agent.tools.get_db") as mock_get_db:
        mock_get_db.return_value.__enter__.return_value = test_db

        result = update_ticket(ticket_id=1, status="resolved")

        assert result.success is True
        assert result.data["status"] == "resolved"


def test_update_ticket_invalid_status(test_db):  # type: ignore
    """Test updating a ticket with invalid status."""
    with patch("agent_chat.agent.tools.get_db") as mock_get_db:
        mock_get_db.return_value.__enter__.return_value = test_db

        result = update_ticket(ticket_id=1, status="invalid")

        assert result.success is False
        assert result.error is not None
        assert "Invalid status" in result.error


def test_execute_tool_success(test_db):  # type: ignore
    """Test successful tool execution via execute_tool."""
    with patch("agent_chat.agent.tools.get_db") as mock_get_db:
        mock_get_db.return_value.__enter__.return_value = test_db

        result, latency = execute_tool("query_customers", {"plan": "enterprise"})

        assert result.success is True
        assert len(result.data) == 1
        assert latency > 0


def test_execute_tool_unknown():
    """Test executing unknown tool."""
    result, latency = execute_tool("unknown_tool", {})

    assert result.success is False
    assert result.error is not None
    assert "Unknown tool" in result.error


def test_execute_tool_invalid_input():
    """Test executing tool with invalid input - missing required field."""
    # create_ticket requires customer_id, subject, description
    result, latency = execute_tool("create_ticket", {"subject": "Test"})

    assert result.success is False
    assert result.error is not None
    assert "Invalid input" in result.error


def test_get_tool_definitions():
    """Test getting tool definitions."""
    definitions = get_tool_definitions()

    assert len(definitions) == 4
    assert any(d["name"] == "query_customers" for d in definitions)
    assert any(d["name"] == "query_tickets" for d in definitions)
    assert any(d["name"] == "create_ticket" for d in definitions)
    assert any(d["name"] == "update_ticket" for d in definitions)
