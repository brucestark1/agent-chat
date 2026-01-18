"""Anthropic Claude model integration."""

from typing import Any

import anthropic

from agent_chat.config import settings
from agent_chat.models.base import BaseModel


class AnthropicModel(BaseModel):
    """Anthropic Claude model integration."""

    def __init__(self) -> None:
        """Initialize the Anthropic client."""
        if settings.anthropic_api_key == "mock":
            raise ValueError(
                "ANTHROPIC_API_KEY is set to 'mock'. "
                "Either set a real API key or use MockModel instead."
            )
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.anthropic_model

    def generate(
        self, messages: list[dict[str, str]], tools: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """Generate a response from Claude.

        Args:
            messages: Conversation history
            tools: Optional tool definitions

        Returns:
            Response dict with either text or tool_call
        """
        # Convert our simple message format to Anthropic format
        api_messages = []
        for msg in messages:
            api_messages.append({"role": msg["role"], "content": msg["content"]})

        # Call Claude
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": api_messages,
        }
        if tools:
            kwargs["tools"] = tools

        response = self.client.messages.create(**kwargs)

        # Parse response
        if response.stop_reason == "tool_use":
            # Find tool use block
            for block in response.content:
                if block.type == "tool_use":
                    return {
                        "type": "tool_call",
                        "name": block.name,
                        "input": block.input,
                        "tool_use_id": block.id,
                    }

        # Text response
        text_content = ""
        for block in response.content:
            if hasattr(block, "text"):
                text_content += block.text

        return {"type": "text", "content": text_content}
