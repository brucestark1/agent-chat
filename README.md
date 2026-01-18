# Agentic Chat Loop MVP

A production-quality agentic chat system built in one day to teach and demonstrate core agentic workflow concepts.

This project implements a complete **tool-using agent loop** with:
- 🤖 Autonomous tool selection and execution
- 💾 Full persistence (Postgres/SQLite)
- 🔄 Multi-turn conversation threading
- 📊 Structured execution traces
- ✅ Production-quality testing and type safety
- 🚀 FastAPI REST + Server-Sent Events (SSE) streaming

## Quick Start

### Prerequisites

- Python 3.11+
- macOS (as specified, but works on Linux too)
- Optional: Anthropic API key (falls back to MockModel)

### Installation (Recommended: uv)

**Using uv** (fastest, recommended):
```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project
uv pip install -e ".[dev]"
uv run pre-commit install
```

**Using pip** (traditional):
```bash
pip install -e ".[dev]"
pre-commit install
```

### Setup Database

The project defaults to SQLite for easy local development:

```bash
# Initialize and seed the database
python -m agent_chat.db.seed
```

**For Postgres** (optional):
```bash
# Update .env file
echo "DATABASE_URL=postgresql://agent:agent123@localhost:5432/agent_chat" > .env

# Start Postgres with Docker Compose
docker compose up -d

# Run seed script
python -m agent_chat.db.seed
```

### Run the Service

```bash
# Using uvicorn directly
uvicorn agent_chat.main:app --reload

# Or using Python module
python -m agent_chat.main
```

The API will be available at http://localhost:8000

## API Usage

### Health Check
```bash
curl http://localhost:8000/healthz
```

### Chat (Non-Streaming)
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me all enterprise customers"
  }'
```

### Chat (Streaming)
```bash
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "message": "Show me all urgent tickets"
  }'
```

### Get Thread History
```bash
curl http://localhost:8000/threads/1
```

### Get Run Trace
```bash
curl http://localhost:8000/runs/1
```

## Development

### Quality Gates

This project uses modern Python tooling:

```bash
# Format code
make fmt

# Lint code
make lint

# Type check
make typecheck

# Run tests
make test

# Run all checks
make check
```

### Project Structure

```
agent-chat/
├── src/agent_chat/
│   ├── agent/          # Core agent loop implementation
│   │   ├── loop.py     # Main agent loop (ReAct pattern)
│   │   ├── tools.py    # Tool definitions and execution
│   │   └── types.py    # Type definitions
│   ├── api/            # FastAPI routes and schemas
│   ├── db/             # Database models and connection
│   ├── models/         # LLM integrations (Anthropic, Mock)
│   ├── config.py       # Settings management
│   └── main.py         # FastAPI application
├── tests/              # Comprehensive test suite
│   ├── test_tools.py
│   ├── test_agent_loop.py
│   └── test_integration.py
├── pyproject.toml      # Modern Python project config
├── Makefile            # Development commands
└── LEARN.md            # Educational content
```

## Configuration

Set environment variables in `.env` file:

```bash
# Database
DATABASE_URL=sqlite:///./agent_chat.db

# Anthropic API (optional - uses MockModel if not set)
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
USE_MOCK_MODEL=false

# Agent settings
MAX_AGENT_ITERATIONS=10
TOOL_TIMEOUT_SECONDS=30

# API settings
API_HOST=0.0.0.0
API_PORT=8000
```

## Available Tools

The agent has access to these tools:

1. **query_customers** - Query customer data by email or plan
2. **query_tickets** - Query support tickets by customer, status, or priority
3. **create_ticket** - Create a new support ticket
4. **update_ticket** - Update ticket status

## Testing

```bash
# Run all tests with coverage
make test

# Run specific test file
pytest tests/test_tools.py -v

# Run with coverage report
pytest --cov=agent_chat --cov-report=html
```

**Test Coverage: 82%** ✅
- 28 passing tests
- Unit tests for tools
- Unit tests for agent loop
- Integration tests for full API

## Architecture Highlights

### Agent Loop (ReAct Pattern)

The core agent loop implements the **ReAct** (Reasoning + Acting) pattern:

1. **Think**: Model receives context and decides next action
2. **Act**: Either call a tool OR provide final answer
3. **Observe**: Tool result is added to conversation context
4. **Repeat**: Loop continues until final answer or max iterations

See `src/agent_chat/agent/loop.py:147` for implementation.

### Persistence

All state is persisted:
- **Threads**: Conversation containers
- **Messages**: User and assistant messages
- **Runs**: Each agent loop execution
- **Tool Calls**: Every tool execution with inputs/outputs/latency

### Streaming

The `/chat/stream` endpoint uses Server-Sent Events (SSE) to stream:
- Each tool call in real-time
- Tool results
- Final answer

Perfect for building responsive UIs that show the agent's "thinking process".

## Technology Stack

- **Python 3.11** - Modern Python with type hints
- **FastAPI** - High-performance async web framework
- **SQLAlchemy 2.0** - Modern ORM with type safety
- **Pydantic v2** - Data validation and settings
- **Anthropic SDK** - Claude API integration
- **Ruff** - Extremely fast linter/formatter (Rust-based)
- **Pyright** - Static type checker
- **Pytest** - Testing framework with async support

## Why This Stack?

All tools are **state-of-the-art as of 2026**:

- **uv**: 10-100x faster than pip ([GitHub](https://github.com/astral-sh/uv))
- **Ruff**: 10-100x faster than Flake8/Black ([Astral](https://astral.sh/ruff))
- **FastAPI**: Best-in-class performance for Python APIs
- **SQLAlchemy 2.0**: Modern async-ready ORM
- **Anthropic Claude**: Leading edge AI models

## Learning More

See **[LEARN.md](LEARN.md)** for:
- Deep dive into agentic workflow concepts
- How the ReAct pattern works
- Tool use best practices
- Production considerations
- Further reading

## License

MIT License - see LICENSE file for details

## Contributing

This is an educational MVP. Feel free to:
- Fork and experiment
- Add new tools
- Improve the agent loop
- Add more sophisticated prompting
- Integrate with vector databases

The goal is learning by building! 🚀

---

Built with ❤️ to demonstrate production-quality agentic systems.
