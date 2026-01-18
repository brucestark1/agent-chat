"""Core agentic loop implementation.

This module contains the main agent loop that:
1. Maintains conversation state
2. Calls the LLM with tool definitions
3. Executes tools when requested
4. Iterates until a final answer or max iterations
5. Persists all state to the database
"""

from datetime import datetime

from sqlalchemy.orm import Session

from agent_chat.agent.tools import execute_tool, get_tool_definitions
from agent_chat.agent.types import AgentStep, AgentTrace
from agent_chat.config import settings
from agent_chat.db.models import Message, Run, Thread, ToolCall
from agent_chat.models.base import BaseModel


class AgentLoop:
    """The core agentic loop that orchestrates tool use and conversation."""

    def __init__(self, model: BaseModel, db: Session):
        """Initialize the agent loop.

        Args:
            model: Language model to use (Anthropic or Mock)
            db: Database session for persistence
        """
        self.model = model
        self.db = db
        self.max_iterations = settings.max_agent_iterations

    def run(self, thread_id: int | None, user_message: str) -> AgentTrace:
        """Run the agent loop for a user message.

        This is the main entry point that:
        1. Creates or retrieves a thread
        2. Loads conversation history
        3. Runs the agentic loop
        4. Persists all results
        5. Returns a structured trace

        Args:
            thread_id: Optional existing thread ID, or None to create new thread
            user_message: The user's message

        Returns:
            AgentTrace with complete execution history
        """
        # Get or create thread
        if thread_id:
            thread = self.db.get(Thread, thread_id)
            if not thread:
                raise ValueError(f"Thread {thread_id} not found")
        else:
            thread = Thread()
            self.db.add(thread)
            self.db.flush()

        # Create user message
        user_msg = Message(thread_id=thread.id, role="user", content=user_message)
        self.db.add(user_msg)
        self.db.flush()

        # Create run record
        run = Run(
            thread_id=thread.id,
            user_message=user_message,
            assistant_message="",  # Will be updated later
            iterations=0,
            status="success",
        )
        self.db.add(run)
        self.db.flush()

        # Run the agent loop
        try:
            steps, final_answer, iterations = self._agent_loop(thread.id, user_message, run.id)

            # Update run with results
            run.assistant_message = final_answer
            run.iterations = iterations
            run.completed_at = datetime.utcnow()

            if iterations >= self.max_iterations:
                run.status = "max_iterations"
            else:
                run.status = "success"

            # Create assistant message
            assistant_msg = Message(thread_id=thread.id, role="assistant", content=final_answer)
            self.db.add(assistant_msg)

            self.db.commit()

            return AgentTrace(
                run_id=run.id,
                thread_id=thread.id,
                iterations=iterations,
                steps=steps,
                final_answer=final_answer,
                status=run.status,  # type: ignore
                error_message=None,
            )

        except Exception as e:
            run.status = "error"
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            self.db.commit()

            return AgentTrace(
                run_id=run.id,
                thread_id=thread.id,
                iterations=0,
                steps=[],
                final_answer="",
                status="error",
                error_message=str(e),
            )

    def _agent_loop(
        self, thread_id: int, user_message: str, run_id: int
    ) -> tuple[list[AgentStep], str, int]:
        """Execute the core agent loop.

        This implements the ReAct pattern:
        - Think (model generates reasoning)
        - Act (model decides to use a tool OR give final answer)
        - Observe (tool result is added to context)
        - Repeat until final answer

        Args:
            thread_id: Thread ID for loading history
            user_message: Current user message
            run_id: Run ID for persisting tool calls

        Returns:
            Tuple of (steps, final_answer, iteration_count)
        """
        steps: list[AgentStep] = []
        tools = get_tool_definitions()

        # Load conversation history (excluding current message)
        history_messages = (
            self.db.query(Message)
            .filter(Message.thread_id == thread_id, Message.content != user_message)
            .order_by(Message.id)
            .all()
        )

        # Build message list for model
        messages: list[dict[str, str]] = []
        for msg in history_messages:
            messages.append({"role": msg.role, "content": msg.content})

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        # Agent loop
        for iteration in range(self.max_iterations):
            # Call model
            response = self.model.generate(messages, tools)

            if response["type"] == "text":
                # Final answer - we're done!
                final_answer = response["content"]
                steps.append(
                    AgentStep(
                        step_type="answer",
                        content=final_answer,
                    )
                )
                return steps, final_answer, iteration + 1

            elif response["type"] == "tool_call":
                # Model wants to use a tool
                tool_name = response["name"]
                tool_input = response["input"]

                # Record tool call step
                steps.append(
                    AgentStep(
                        step_type="tool_call",
                        content=f"Calling tool: {tool_name}",
                        tool_name=tool_name,
                        tool_input=tool_input,
                    )
                )

                # Execute tool
                result, latency_ms = execute_tool(tool_name, tool_input)

                # Persist tool call
                tool_call = ToolCall(
                    run_id=run_id,
                    tool_name=tool_name,
                    tool_input=tool_input,
                    tool_output=result.data if result.success else None,
                    error=result.error if not result.success else None,
                    latency_ms=latency_ms,
                )
                self.db.add(tool_call)
                self.db.flush()

                # Record tool result step
                steps.append(
                    AgentStep(
                        step_type="tool_result",
                        content=f"Tool result: {result.model_dump_json()}",
                        tool_name=tool_name,
                        tool_output=result.model_dump(),
                    )
                )

                # Add tool result to conversation
                # For Anthropic, we need to structure it properly
                messages.append(
                    {
                        "role": "assistant",
                        "content": f"I'll use the {tool_name} tool with input: {tool_input}",
                    }
                )
                messages.append(
                    {"role": "user", "content": f"Tool result: {result.model_dump_json()}"}
                )

        # Max iterations reached
        final_answer = "I apologize, but I've reached the maximum number of iterations without completing the task. Please try rephrasing your request."
        steps.append(
            AgentStep(
                step_type="answer",
                content=final_answer,
            )
        )
        return steps, final_answer, self.max_iterations
