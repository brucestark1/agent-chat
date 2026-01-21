"""Integration tests for the full chat flow."""

from fastapi.testclient import TestClient

from agent_chat.config import settings
from agent_chat.main import app

# Ensure we use mock model for tests
settings.use_mock_model = True

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model"] == "mock"


def test_chat_new_thread():
    """Test chat with new thread."""
    response = client.post("/chat", json={"message": "Tell me about customers"})

    assert response.status_code == 200
    data = response.json()

    assert "thread_id" in data
    assert "assistant_message" in data
    assert "trace" in data
    assert data["thread_id"] > 0
    assert len(data["assistant_message"]) > 0


def test_chat_existing_thread():
    """Test chat with existing thread."""
    # Create first message
    response1 = client.post("/chat", json={"message": "Hello"})
    assert response1.status_code == 200
    thread_id = response1.json()["thread_id"]

    # Send second message in same thread
    response2 = client.post("/chat", json={"message": "Show me tickets", "thread_id": thread_id})
    assert response2.status_code == 200
    data2 = response2.json()

    assert data2["thread_id"] == thread_id


def test_get_thread():
    """Test getting thread data."""
    # Create a thread
    chat_response = client.post("/chat", json={"message": "Test message"})
    thread_id = chat_response.json()["thread_id"]

    # Get thread
    response = client.get(f"/threads/{thread_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["thread_id"] == thread_id
    assert len(data["messages"]) >= 2  # User + assistant


def test_get_thread_not_found():
    """Test getting non-existent thread."""
    response = client.get("/threads/99999")
    assert response.status_code == 404


def test_get_run():
    """Test getting run data."""
    # Create a run
    chat_response = client.post("/chat", json={"message": "Test message"})
    trace = chat_response.json()["trace"]
    run_id = trace["run_id"]

    # Get run
    response = client.get(f"/runs/{run_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["run_id"] == run_id
    assert data["status"] in ["success", "error", "max_iterations"]
    assert "tool_calls" in data


def test_get_run_not_found():
    """Test getting non-existent run."""
    response = client.get("/runs/99999")
    assert response.status_code == 404


def test_chat_stream():
    """Test streaming chat endpoint."""
    response = client.post(
        "/chat/stream",
        json={"message": "Tell me about customers"},
        headers={"Accept": "text/event-stream"},
    )

    assert response.status_code == 200
    # Verify we get SSE events
    content = response.text
    assert "event:" in content
    assert "data:" in content


def test_full_conversation_flow():
    """Test a complete multi-turn conversation."""
    # Turn 1: Ask about customers
    response1 = client.post("/chat", json={"message": "Show me enterprise customers"})
    assert response1.status_code == 200
    data1 = response1.json()
    thread_id = data1["thread_id"]

    # Turn 2: Ask about tickets
    response2 = client.post(
        "/chat", json={"message": "Now show me urgent tickets", "thread_id": thread_id}
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["thread_id"] == thread_id

    # Verify thread has all messages
    thread_response = client.get(f"/threads/{thread_id}")
    thread_data = thread_response.json()
    messages = thread_data["messages"]

    # Should have: user1, assistant1, user2, assistant2
    assert len(messages) >= 4
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
