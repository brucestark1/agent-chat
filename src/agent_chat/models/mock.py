"""Mock model for local testing without API key."""

from typing import Any

from agent_chat.models.base import BaseModel


class MockModel(BaseModel):
    """Mock model that simulates agent behavior for testing.

    This model follows a simple pattern:
    1. If the user asks about customers -> call query_customers
    2. If the user asks about tickets -> call query_tickets
    3. Otherwise -> return a canned response
    """

    def __init__(self) -> None:
        """Initialize mock model."""
        self.call_count = 0

    def generate(
        self, messages: list[dict[str, str]], tools: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """Generate a mock response based on simple patterns.

        Args:
            messages: Conversation history
            tools: Optional tool definitions (used to know what tools are available)

        Returns:
            Response dict with either text or tool_call
        """
        self.call_count += 1

        # Get the last user message
        last_message = messages[-1]["content"].lower() if messages else ""

        # Simple pattern matching for tool calls
        # On first call, decide to use a tool based on keywords
        if self.call_count == 1:
            if "customer" in last_message or "alice" in last_message or "bob" in last_message:
                return {
                    "type": "tool_call",
                    "name": "query_customers",
                    "input": {},
                    "tool_use_id": "mock_tool_1",
                }
            elif "ticket" in last_message or "support" in last_message:
                return {
                    "type": "tool_call",
                    "name": "query_tickets",
                    "input": {"status": "open"},
                    "tool_use_id": "mock_tool_2",
                }
            elif "create" in last_message and "ticket" in last_message:
                return {
                    "type": "tool_call",
                    "name": "create_ticket",
                    "input": {
                        "customer_id": 1,
                        "subject": "Mock ticket",
                        "description": "This is a mock ticket created by the mock model",
                        "priority": "medium",
                    },
                    "tool_use_id": "mock_tool_3",
                }

        # On subsequent calls, return a final answer
        # Look for tool result in message history
        tool_result = None
        for msg in reversed(messages):
            if "tool_result" in msg.get("content", ""):
                try:
                    # Try to extract the tool result
                    content = msg["content"]
                    if "success" in content:
                        tool_result = content
                        break
                except Exception:
                    pass

        if tool_result:
            return {
                "type": "text",
                "content": (
                    "Based on the information I retrieved, I can help you with that. "
                    "The tool returned the relevant data which shows the current state of the system."
                ),
            }

        return {
            "type": "text",
            "content": (
                "I'm a mock model for testing. I can simulate tool calls and responses. "
                "Try asking me about customers, tickets, or creating a ticket!"
            ),
        }
