# Quick Reference Guide: Agentic Systems

A rapid-fire reference for terminology, concepts, commands, and anti-patterns to remember.

## 🔑 Core Terminology

### Agentic System
An AI system that **reasons**, **acts**, **observes**, and **iterates** autonomously to complete tasks.

### ReAct Pattern
**Re**asoning + **Act**ing: The core agent loop pattern.
- Think → Act (or Answer) → Observe → Repeat

### Tool
An action the agent can perform (database query, API call, computation).

### Thread
A conversation container that holds multi-turn dialogue history.

### Run
A single execution of the agent loop (one POST /chat call).

### Trace
Complete record of an agent's execution (steps, tool calls, results).

### Stopping Condition
Rules that determine when the agent loop terminates:
1. Final answer from model
2. Max iterations reached
3. Error occurred

### Tool Call
When the model decides to use a tool instead of answering directly.

### Observation
The result of a tool call, fed back into the agent's context.

---

## 🧠 Key Concepts to Remember

### 1. The Agent Loop
```python
while not done:
    response = model.generate(context)
    if response.is_final_answer:
        return answer
    else:
        result = execute_tool(response.tool_call)
        context.append(result)  # CRITICAL: Feed result back!
```

### 2. Tool Execution Must Be Safe
- ✅ **ALWAYS** validate inputs (use Pydantic)
- ✅ **ALWAYS** handle errors gracefully
- ✅ **ALWAYS** set timeouts
- ✅ **ALWAYS** log everything
- ❌ **NEVER** trust agent input blindly

### 3. Context Window Management
**Problem**: Conversations get too long for LLM context.

**Solutions**:
- Summarization (compress old messages)
- Rolling window (keep only recent N messages)
- Semantic compression (extract key facts)

### 4. Max Iterations Is Critical
**Without it**: Infinite loops, wasted money, hanging requests.

**With it**: Safety net prevents runaway agents.

**Typical values**: 5-20 depending on task complexity.

### 5. Tools Need Good Descriptions
The model chooses tools based on descriptions!

**Bad**: `"query_db"` → Model doesn't know what it queries
**Good**: `"Query customer database by email or plan type"` → Clear!

### 6. Streaming Shows Progress
Users see the agent "thinking" in real-time:
- "I'll query customers..."
- "Found 3 customers"
- "Now checking their tickets..."
- "Here's the result..."

Much better UX than a 30-second wait!

---

## 💾 Database Schema Quick View

```
threads
├── id (int)
├── created_at
├── updated_at
└── [has many] messages
    └── [has many] runs

messages
├── id (int)
├── thread_id (FK)
├── role (user/assistant)
├── content (text)
└── created_at

runs
├── id (int)
├── thread_id (FK)
├── user_message
├── assistant_message
├── iterations (int)
├── status (success/error/max_iterations)
├── created_at
├── completed_at
└── [has many] tool_calls

tool_calls
├── id (int)
├── run_id (FK)
├── tool_name
├── tool_input (JSON)
├── tool_output (JSON)
├── error (text)
├── latency_ms (int)
└── created_at
```

---

## ⚡ Common Commands

### Development
```bash
# Install dependencies (recommended: uv)
uv pip install -e ".[dev]"

# Install dependencies (traditional pip)
pip install -e ".[dev]"

# Setup pre-commit hooks
pre-commit install

# Format code
make fmt

# Lint code
make lint

# Type check
make typecheck

# Run tests
make test

# Run ALL quality gates
make check
```

### Database
```bash
# Initialize and seed database
python -m agent_chat.db.seed

# For Postgres (if using Docker)
docker compose up -d
```

### Running
```bash
# Start API server
uvicorn agent_chat.main:app --reload

# Start on custom port
uvicorn agent_chat.main:app --port 8080

# Production mode (no reload)
uvicorn agent_chat.main:app --host 0.0.0.0
```

### Testing
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_tools.py

# Run with coverage report
python -m pytest --cov=agent_chat --cov-report=html

# Run specific test
python -m pytest tests/test_tools.py::test_query_customers_all -v
```

### API Calls
```bash
# Health check
curl http://localhost:8000/healthz

# Chat (new thread)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me all customers"}'

# Chat (existing thread)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Now show tickets", "thread_id": 1}'

# Streaming chat
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message": "Find urgent tickets"}'

# Get thread history
curl http://localhost:8000/threads/1

# Get run trace
curl http://localhost:8000/runs/1
```

---

## 🚨 Anti-Patterns to Avoid

### ❌ No Max Iterations
**Problem**: Agent loops forever.
**Fix**: Always set `max_iterations` (default: 10).

### ❌ No Input Validation
**Problem**: SQL injection, crashes, security holes.
**Fix**: Use Pydantic schemas for every tool input.

### ❌ No Error Handling
**Problem**: One tool failure crashes entire agent.
**Fix**: Wrap tool execution in try/except, return ToolResult.

### ❌ No Observability
**Problem**: Can't debug what the agent did.
**Fix**: Log and persist every tool call with inputs/outputs.

### ❌ Trusting Agent Output Blindly
**Problem**: Agent might hallucinate tool calls, invalid inputs.
**Fix**: Validate everything at the tool boundary.

### ❌ Ignoring Context Window Limits
**Problem**: Conversations get too long, requests fail.
**Fix**: Implement summarization or rolling window.

### ❌ No Timeout on Tools
**Problem**: One slow tool hangs entire request.
**Fix**: Set timeouts on all tool executions.

### ❌ Poor Tool Descriptions
**Problem**: Model can't choose the right tool.
**Fix**: Write clear, specific descriptions with examples.

### ❌ No Rate Limiting
**Problem**: Agent spams tools/APIs, gets banned.
**Fix**: Implement rate limits and backoff.

### ❌ Mixing User Input and System Prompts
**Problem**: Prompt injection attacks.
**Fix**: Separate user messages from system instructions.

---

## 🎯 Best Practices Checklist

### Tool Design
- [ ] Clear, descriptive name
- [ ] Detailed description (what it does, when to use it)
- [ ] Pydantic schema for input validation
- [ ] Structured output (ToolResult with success/error)
- [ ] Error handling (try/except)
- [ ] Timeout implementation
- [ ] Logging/persistence

### Agent Loop
- [ ] Max iterations set (5-20 typical)
- [ ] Clear stopping conditions
- [ ] Tool results fed back to context
- [ ] Error handling at loop level
- [ ] Trace/logging for debugging

### Security
- [ ] Input validation (Pydantic)
- [ ] SQL injection prevention (parameterized queries)
- [ ] Rate limiting (per-user, per-tool)
- [ ] Audit logging (all tool calls)
- [ ] Least privilege (tools only access what needed)
- [ ] Timeout enforcement

### Observability
- [ ] Log every tool call
- [ ] Track latencies
- [ ] Persist traces
- [ ] Error tracking
- [ ] Token usage monitoring

### Testing
- [ ] Unit tests for each tool
- [ ] Agent loop tests
- [ ] Integration tests (full flow)
- [ ] MockModel for testing
- [ ] Error case coverage

---

## 📊 Performance Tips

### Latency Optimization
1. **Parallel tool calls** (when independent)
2. **Streaming** for better perceived performance
3. **Caching** for repeated queries
4. **Smaller models** for simple tasks

### Cost Optimization
1. **Track tokens** per request
2. **Use MockModel** for development
3. **Cache responses** when possible
4. **Set budgets** per user/session
5. **Cheaper models** for tool selection

### Scaling
1. **Database connection pooling**
2. **Async/await** for concurrent requests
3. **Redis for session state**
4. **Load balancing**
5. **Horizontal scaling** (stateless design)

---

## 🔧 Debugging Tips

### Agent Not Using Tools
- Check tool descriptions (be explicit!)
- Verify tools are in tool list
- Look at prompt engineering
- Check model's reasoning in trace

### Agent Loops Forever
- Check max_iterations is set
- Look for tool result formatting issues
- Verify stopping condition logic

### Tools Failing
- Check input validation errors
- Look at error logs
- Verify database connections
- Check API credentials

### Tests Failing
- Read error messages carefully
- Check test database setup
- Verify mocks are configured
- Run individual tests: `pytest tests/test_file.py::test_name -v`

### Type Errors
- Run `pyright src tests` to see all errors
- Check function signatures
- Verify Pydantic models
- Look for None handling

---

## 📚 Important File Locations

```
src/agent_chat/
├── agent/loop.py          # Line 147-239: Core agent loop
├── agent/tools.py         # Line 257-285: execute_tool function
├── agent/tools.py         # Line 289-306: get_tool_definitions
├── config.py              # All configuration settings
├── main.py                # Line 77-97: Chat endpoint
└── db/models.py           # Database schema

tests/
├── conftest.py            # Test fixtures
├── test_tools.py          # Tool unit tests
├── test_agent_loop.py     # Agent loop tests
└── test_integration.py    # Full API tests
```

---

## 🎓 Mental Models

### Think of an Agent as a Junior Developer
- Needs clear instructions (tool descriptions)
- Makes mistakes (input validation needed)
- Needs feedback (tool results)
- Has limits (max iterations)
- Needs supervision (error handling)

### ReAct = Scientific Method
1. **Hypothesis** (model thinks what to do)
2. **Experiment** (execute tool)
3. **Observation** (see result)
4. **Iterate** (use result to think next step)

### Tools = Agent's Hands
- Without tools: Agent can only talk
- With tools: Agent can **do things**
- More tools ≠ better (keep focused!)

### Context Window = Working Memory
- Limited space
- Older memories fade (summarization)
- Important facts must persist (database)

---

## 🆘 Quick Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Agent gives up immediately | No tools provided | Check `get_tool_definitions()` |
| Agent doesn't use right tool | Poor description | Make descriptions more specific |
| Tool execution fails | Input validation error | Check Pydantic schema matches input |
| Request times out | No max_iterations | Set max_iterations (default: 10) |
| Context too long error | Thread too old | Implement summarization |
| Tests import error | Wrong Python path | Use `python -m pytest` |
| Type check fails | Missing type hints | Add return types and param types |
| Database error | Not initialized | Run `python -m agent_chat.db.seed` |

---

## 🎯 One-Sentence Reminders

1. **Always validate tool inputs** - Agents can send anything!
2. **Always set max_iterations** - Prevents infinite loops.
3. **Always feed tool results back** - That's how learning happens!
4. **Always log everything** - You'll need it for debugging.
5. **Always handle errors** - Tools fail, be ready.
6. **Clear descriptions matter** - Model chooses based on them.
7. **Test with MockModel first** - Save API credits.
8. **Streaming improves UX** - Users see progress.
9. **Context has limits** - Summarize or truncate.
10. **Security is critical** - Validate, audit, limit access.

---

## 📖 Quick Reads (5 min each)

From **LEARN.md**:
- Section: "What is an Agentic System?" (page 1)
- Section: "The ReAct Pattern" (page 2-3)
- Section: "Tool Use" (page 4-5)
- Section: "Production Considerations" (page 8-10)

From **README.md**:
- Section: "Architecture Highlights" (page 6)
- Section: "Available Tools" (page 5)

---

## 🚀 Getting Started in 3 Minutes

```bash
# 1. Install (30 sec)
pip install -e ".[dev]"

# 2. Setup database (10 sec)
python -m agent_chat.db.seed

# 3. Run tests (verify it works) (30 sec)
make check

# 4. Start server (10 sec)
uvicorn agent_chat.main:app --reload

# 5. Test it! (60 sec)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me all urgent tickets"}'
```

---

## 🔗 External Resources

- **Python 3.14 Release**: [Python.org](https://www.python.org/downloads/)
- **Anthropic Tool Use**: [Docs](https://docs.anthropic.com/claude/docs/tool-use)
- **ReAct Paper**: [arXiv:2210.03629](https://arxiv.org/abs/2210.03629)
- **FastAPI Docs**: [FastAPI](https://fastapi.tiangolo.com/)
- **Ruff Linter**: [Astral.sh](https://astral.sh/ruff)
- **uv Package Manager**: [GitHub](https://github.com/astral-sh/uv)

---

**Remember**: This is a learning MVP. The goal is to understand agentic patterns by building them. Experiment, break things, learn! 🚀
