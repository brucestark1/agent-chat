"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sse_starlette.sse import EventSourceResponse

from agent_chat.agent.loop import AgentLoop
from agent_chat.api.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    RunResponse,
    ThreadResponse,
)
from agent_chat.config import settings
from agent_chat.db.connection import get_db, init_db
from agent_chat.db.models import Run, Thread
from agent_chat.models.anthropic_model import AnthropicModel
from agent_chat.models.base import BaseModel
from agent_chat.models.mock import MockModel


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    """Lifespan context manager for startup/shutdown events."""
    # Startup: Initialize database
    init_db()
    print("✓ Database initialized")
    yield
    # Shutdown: cleanup if needed
    print("✓ Shutting down")


# Create FastAPI app
app = FastAPI(
    title="Agentic Chat Loop MVP",
    description="Production-quality agentic chat system with tool use",
    version="0.1.0",
    lifespan=lifespan,
)


def get_model() -> BaseModel:
    """Get the appropriate model based on configuration."""
    if settings.use_mock_model or settings.anthropic_api_key == "mock":
        return MockModel()
    return AnthropicModel()


@app.get("/healthz", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        Health status of the service
    """
    # Check database
    try:
        with get_db() as db:
            db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {e}"

    # Check model
    model_type = (
        "mock" if settings.use_mock_model or settings.anthropic_api_key == "mock" else "anthropic"
    )

    return HealthResponse(status="healthy", database=db_status, model=model_type)


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Main chat endpoint - runs the agentic loop.

    Args:
        request: Chat request with message and optional thread_id

    Returns:
        Chat response with assistant message and execution trace
    """
    try:
        model = get_model()
        with get_db() as db:
            agent = AgentLoop(model, db)
            trace = agent.run(request.thread_id, request.message)

        return ChatResponse(
            thread_id=trace.thread_id,
            assistant_message=trace.final_answer,
            trace=trace.model_dump(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> EventSourceResponse:
    """Streaming chat endpoint with Server-Sent Events.

    This endpoint streams the agent's thinking process in real-time:
    - Each tool call
    - Each tool result
    - Final answer

    Args:
        request: Chat request with message and optional thread_id

    Returns:
        SSE stream of agent steps
    """

    async def event_generator():  # type: ignore
        """Generate SSE events for agent steps."""
        try:
            model = get_model()
            with get_db() as db:
                agent = AgentLoop(model, db)

                # For now, we'll run the full loop and stream the steps
                # In production, you'd refactor AgentLoop to support streaming
                trace = agent.run(request.thread_id, request.message)

                # Stream each step
                for step in trace.steps:
                    yield {"event": "step", "data": step.model_dump_json()}

                # Stream final result
                yield {
                    "event": "complete",
                    "data": trace.model_dump_json(),
                }

        except Exception as e:
            yield {"event": "error", "data": str(e)}

    return EventSourceResponse(event_generator())


@app.get("/threads/{thread_id}", response_model=ThreadResponse)
def get_thread(thread_id: int) -> ThreadResponse:
    """Get a conversation thread with all messages.

    Args:
        thread_id: ID of the thread to retrieve

    Returns:
        Thread data with messages
    """
    with get_db() as db:
        thread = db.get(Thread, thread_id)
        if not thread:
            raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

        messages = [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in thread.messages
        ]

        return ThreadResponse(
            thread_id=thread.id,
            created_at=thread.created_at.isoformat(),
            updated_at=thread.updated_at.isoformat(),
            messages=messages,
        )


@app.get("/runs/{run_id}", response_model=RunResponse)
def get_run(run_id: int) -> RunResponse:
    """Get a complete run trace with all tool calls.

    Args:
        run_id: ID of the run to retrieve

    Returns:
        Complete run data with tool call details
    """
    with get_db() as db:
        run = db.get(Run, run_id)
        if not run:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

        tool_calls = [
            {
                "id": tc.id,
                "tool_name": tc.tool_name,
                "tool_input": tc.tool_input,
                "tool_output": tc.tool_output,
                "error": tc.error,
                "latency_ms": tc.latency_ms,
                "created_at": tc.created_at.isoformat(),
            }
            for tc in run.tool_calls
        ]

        return RunResponse(
            run_id=run.id,
            thread_id=run.thread_id,
            user_message=run.user_message,
            assistant_message=run.assistant_message,
            iterations=run.iterations,
            status=run.status,
            error_message=run.error_message,
            tool_calls=tool_calls,
            created_at=run.created_at.isoformat(),
            completed_at=run.completed_at.isoformat() if run.completed_at else None,
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
