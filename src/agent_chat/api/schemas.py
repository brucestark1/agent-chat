"""Pydantic schemas for API request/response validation."""

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema for /chat endpoint."""

    message: str = Field(..., description="User message")
    thread_id: int | None = Field(None, description="Optional thread ID to continue conversation")


class ChatResponse(BaseModel):
    """Response schema for /chat endpoint."""

    thread_id: int
    assistant_message: str
    trace: dict[str, Any]


class ThreadResponse(BaseModel):
    """Response schema for /threads/{id} endpoint."""

    thread_id: int
    created_at: str
    updated_at: str
    messages: list[dict[str, Any]]


class RunResponse(BaseModel):
    """Response schema for /runs/{id} endpoint."""

    run_id: int
    thread_id: int
    user_message: str
    assistant_message: str
    iterations: int
    status: str
    error_message: str | None
    tool_calls: list[dict[str, Any]]
    created_at: str
    completed_at: str | None


class HealthResponse(BaseModel):
    """Response schema for /healthz endpoint."""

    status: str
    database: str
    model: str
