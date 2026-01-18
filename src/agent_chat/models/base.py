"""Base model interface for agent interactions."""

from abc import ABC, abstractmethod
from typing import Any


class BaseModel(ABC):
    """Abstract base class for language model integrations."""

    @abstractmethod
    def generate(
        self, messages: list[dict[str, str]], tools: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """Generate a response from the model.

        Args:
            messages: Conversation history in format [{"role": "user"|"assistant", "content": str}]
            tools: Optional list of tool definitions

        Returns:
            Response dict with either:
            - {"type": "text", "content": str} for final answers
            - {"type": "tool_call", "name": str, "input": dict} for tool calls
        """
        pass
