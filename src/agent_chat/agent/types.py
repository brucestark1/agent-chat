"""Type definitions for the agent system."""

from typing import Any, Literal

from pydantic import BaseModel


class ToolInput(BaseModel):
    """Base class for tool input validation."""

    pass


class ToolResult(BaseModel):
    """Result of a tool execution."""

    success: bool
    data: Any = None
    error: str | None = None


class AgentStep(BaseModel):
    """A single step in the agent loop."""

    step_type: Literal["thought", "tool_call", "tool_result", "answer"]
    content: str
    tool_name: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_output: dict[str, Any] | None = None


class AgentTrace(BaseModel):
    """Complete trace of an agent run."""

    run_id: int
    thread_id: int
    iterations: int
    steps: list[AgentStep]
    final_answer: str
    status: Literal["success", "error", "max_iterations"]
    error_message: str | None = None
