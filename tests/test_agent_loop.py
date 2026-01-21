"""Unit tests for the agent loop."""

from agent_chat.agent.loop import AgentLoop
from agent_chat.models.mock import MockModel


def test_agent_loop_basic(test_db):  # type: ignore
    """Test basic agent loop execution."""
    model = MockModel()
    agent = AgentLoop(model, test_db)

    trace = agent.run(None, "Tell me about customers")

    assert trace.thread_id > 0
    assert trace.status == "success"
    assert trace.iterations > 0
    assert len(trace.steps) > 0
    assert trace.final_answer


def test_agent_loop_with_thread(test_db):  # type: ignore
    """Test agent loop with existing thread."""
    model = MockModel()
    agent = AgentLoop(model, test_db)

    # First message
    trace1 = agent.run(None, "Hello")
    thread_id = trace1.thread_id

    # Second message in same thread
    trace2 = agent.run(thread_id, "Tell me about tickets")

    assert trace2.thread_id == thread_id
    assert trace2.status == "success"


def test_agent_loop_tool_execution(test_db):  # type: ignore
    """Test that agent loop properly executes tools."""
    model = MockModel()
    agent = AgentLoop(model, test_db)

    trace = agent.run(None, "Show me all customers")

    # Should have at least one tool call step
    tool_steps = [s for s in trace.steps if s.step_type == "tool_call"]
    assert len(tool_steps) > 0

    # Should have tool results
    result_steps = [s for s in trace.steps if s.step_type == "tool_result"]
    assert len(result_steps) > 0


def test_agent_loop_persistence(test_db):  # type: ignore
    """Test that agent loop persists data correctly."""
    from agent_chat.db.models import Message, Run, Thread

    model = MockModel()
    agent = AgentLoop(model, test_db)

    trace = agent.run(None, "Test message")

    # Check thread was created
    thread = test_db.get(Thread, trace.thread_id)
    assert thread is not None

    # Check messages were created
    messages = test_db.query(Message).filter(Message.thread_id == trace.thread_id).all()
    assert len(messages) >= 2  # At least user + assistant

    # Check run was created
    run = test_db.get(Run, trace.run_id)
    assert run is not None
    assert run.status == trace.status
    assert run.iterations == trace.iterations


def test_agent_loop_max_iterations(test_db):  # type: ignore
    """Test that agent loop respects max iterations."""
    model = MockModel()
    agent = AgentLoop(model, test_db)
    agent.max_iterations = 2

    # Mock model will keep calling tools if we give it the right prompt
    # But it should stop at max iterations
    trace = agent.run(None, "Show me customers")

    # With max_iterations=2, we might hit the limit depending on model behavior
    # Just verify the trace is valid
    assert trace.status in ["success", "max_iterations"]
    assert trace.iterations <= agent.max_iterations
