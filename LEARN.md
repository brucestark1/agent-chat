# Learning Guide: Agentic Workflows

This document explains the core concepts behind agentic systems and how they're implemented in this project.

## Table of Contents

1. [What is an Agentic System?](#what-is-an-agentic-system)
2. [The ReAct Pattern](#the-react-pattern)
3. [Tool Use](#tool-use)
4. [Conversation Threading](#conversation-threading)
5. [Stopping Conditions](#stopping-conditions)
6. [Production Considerations](#production-considerations)
7. [Further Reading](#further-reading)

## What is an Agentic System?

An **agentic system** is an AI system that can:
1. **Reason** about what to do next
2. **Act** by using tools or taking actions
3. **Observe** the results
4. **Iterate** until completing the task

Unlike simple chatbots that just respond, agents are **goal-oriented** and can break down complex tasks into steps.

### Example Flow

**User**: "Find all urgent tickets for enterprise customers and update them to in-progress"

**Agent**:
1. 🤔 Thinks: "I need to first find enterprise customers"
2. 🔧 Uses: `query_customers(plan="enterprise")`
3. 👀 Observes: Got customer IDs [1, 5, 7]
4. 🤔 Thinks: "Now find urgent tickets for these customers"
5. 🔧 Uses: `query_tickets(priority="urgent")`
6. 👀 Observes: Got tickets [101, 103]
7. 🤔 Thinks: "Now update each ticket"
8. 🔧 Uses: `update_ticket(101, "in_progress")`
9. 🔧 Uses: `update_ticket(103, "in_progress")`
10. ✅ Responds: "I've updated 2 urgent tickets to in-progress"

This multi-step reasoning and acting is what makes it "agentic".

## The ReAct Pattern

**ReAct** (Reasoning + Acting) is the most popular pattern for building agents.

### Core Loop

```python
while not done:
    # 1. REASON: Think about what to do
    response = model.generate(context + history)

    if response.is_final_answer:
        # 2. DONE: Return answer
        return response.answer

    if response.is_tool_call:
        # 3. ACT: Execute the tool
        result = execute_tool(response.tool_name, response.tool_input)

        # 4. OBSERVE: Add result to context
        history.append(("tool_result", result))

        # 5. REPEAT: Go back to step 1
        continue
```

### Key Insight

The model gets to see the **results of its actions** before deciding what to do next. This creates a feedback loop that enables complex, multi-step reasoning.

### Implementation

See `src/agent_chat/agent/loop.py:147-239` for our implementation:

```python
for iteration in range(self.max_iterations):
    response = self.model.generate(messages, tools)

    if response["type"] == "text":
        # Final answer - done!
        return steps, final_answer, iteration + 1

    elif response["type"] == "tool_call":
        # Execute tool
        result, latency = execute_tool(...)

        # Add to conversation
        messages.append(tool_result)

        # Continue loop
```

## Tool Use

Tools are the agent's **interface to the world**. They let the agent:
- Query databases
- Call APIs
- Perform computations
- Take actions

### Anatomy of a Tool

Every tool needs:

1. **Name**: What the tool is called
2. **Description**: What it does (helps the model choose)
3. **Input Schema**: What parameters it takes (with validation)
4. **Function**: The actual implementation

Example from `src/agent_chat/agent/tools.py:159-181`:

```python
# 1. Input Schema (Pydantic)
class QueryTicketsInput(BaseModel):
    customer_id: int | None = Field(None, description="Filter by customer ID")
    status: str | None = Field(None, description="Filter by status")
    priority: str | None = Field(None, description="Filter by priority")

# 2. Function Implementation
def query_tickets(
    customer_id: int | None = None,
    status: str | None = None,
    priority: str | None = None,
) -> ToolResult:
    """Query support tickets from the database."""
    # ... implementation

# 3. Tool Registry
TOOLS = {
    "query_tickets": {
        "function": query_tickets,
        "schema": QueryTicketsInput,
        "description": "Query support tickets by customer, status, or priority",
    },
}
```

### Why Input Validation Matters

Input validation prevents the agent from:
- Passing invalid data types
- Missing required parameters
- SQL injection attacks
- Breaking your database

**Always validate tool inputs!**

### Tool Execution

Our `execute_tool` function (`src/agent_chat/agent/tools.py:257-285`):
1. Validates the tool exists
2. Validates the input against the schema
3. Executes the tool function
4. Measures latency
5. Returns structured result (success/error)

This ensures **safe, observable tool execution**.

## Conversation Threading

Threads let users have **multi-turn conversations** where the agent remembers context.

### Database Schema

```sql
threads
  └─ messages (user/assistant messages)
  └─ runs (each agent execution)
      └─ tool_calls (tools used in this run)
```

### How It Works

1. **First message**: Creates a new thread
2. **Subsequent messages**: Use the same thread_id
3. **Agent sees history**: All previous messages are included in context
4. **Context builds up**: Agent can reference earlier conversation

Example:

```
User: "Who is alice@example.com?"
Agent: [queries DB] "Alice is an enterprise customer..."

User: "Show me her tickets"  ← Agent remembers "her" = Alice
Agent: [queries tickets for Alice's customer_id]
```

### Implementation

See `src/agent_chat/agent/loop.py:163-187`:

```python
# Load conversation history
history_messages = db.query(Message).filter(
    Message.thread_id == thread_id
).order_by(Message.id).all()

# Build context
messages = []
for msg in history_messages:
    messages.append({"role": msg.role, "content": msg.content})
```

## Stopping Conditions

**Critical**: Agents must know when to stop!

### Three Stop Conditions

1. **Final Answer**: Model decides it's done and returns text
2. **Max Iterations**: Safety limit (prevents infinite loops)
3. **Error**: Something went wrong

### Why Max Iterations?

Without a limit, bugs can cause:
- Infinite loops burning API credits
- Hanging requests
- Resource exhaustion

**Always set a reasonable max_iterations!**

### Our Implementation

```python
MAX_AGENT_ITERATIONS = 10  # Configurable

for iteration in range(self.max_iterations):
    # ... agent loop

    if iteration >= self.max_iterations:
        return "Max iterations reached"
```

In production, consider:
- Different limits for different tasks
- Exponential backoff
- User-facing iteration indicators

## Production Considerations

### 1. Observability

**Problem**: Agents are black boxes - hard to debug.

**Solution**: Log everything!
- Every tool call with inputs/outputs
- Latencies
- Errors
- Model responses

Our implementation: `ToolCall` model persists all this.

### 2. Error Handling

**Problem**: Tools can fail (network, DB, validation).

**Solution**: Graceful error handling:
```python
try:
    result = execute_tool(...)
except Exception as e:
    return ToolResult(success=False, error=str(e))
```

The agent sees the error and can:
- Try again with different inputs
- Use a different approach
- Inform the user

### 3. Security

**Critical**: Agents can access sensitive systems!

**Best practices**:
1. ✅ **Input validation** (we use Pydantic)
2. ✅ **Least privilege** (tools only access what they need)
3. ✅ **Rate limiting** (prevent abuse)
4. ✅ **Audit logs** (we persist all tool calls)
5. ⚠️ **Sandboxing** (not implemented in MVP)

### 4. Latency

**Problem**: Multiple LLM calls = slow responses.

**Solutions**:
- **Streaming** (we have `/chat/stream`)
- **Parallel tool execution** (future enhancement)
- **Caching** (for repeated queries)
- **Smaller models** for simple tasks

### 5. Cost

**Problem**: LLM calls add up fast.

**Monitoring**:
- Track tokens per request
- Set per-user budgets
- Use cheaper models when possible

**Our approach**: MockModel for development/testing.

### 6. Prompt Engineering

**Key insight**: The system prompt matters!

Best practices:
- Be explicit about when to stop
- Show examples of good tool use
- Explain available tools clearly
- Set expectations for output format

### 7. Testing

**Challenge**: Non-deterministic behavior.

**Our approach**:
- ✅ Unit tests for tools (deterministic)
- ✅ Integration tests with MockModel
- ⚠️ E2E tests with real model (not in MVP)

## Architecture Patterns

### 1. Hand-Rolled vs Framework

**This project**: Hand-rolled agent loop

**Pros**:
- Full control
- Easy to understand
- No framework lock-in

**Cons**:
- More code to maintain
- Missing advanced features

**Frameworks to consider**:
- LangChain/LangGraph
- Semantic Kernel
- AutoGPT
- CrewAI

### 2. Synchronous vs Asynchronous

**This project**: Synchronous (simpler)

**For production**: Consider async:
```python
async def agent_loop():
    async with aiohttp.ClientSession() as session:
        # Parallel tool calls
        results = await asyncio.gather(
            call_tool_1(),
            call_tool_2(),
        )
```

### 3. Stateless vs Stateful

**This project**: Stateful (DB persistence)

**Alternative**: Stateless with external state store (Redis, etc.)

## Advanced Topics

### Chain of Thought (CoT)

Make the model show its reasoning:

```
User: "Find urgent tickets"

Agent: "Let me break this down:
1. First, I'll query tickets with priority='urgent'
2. Then format the results
[calls query_tickets tool]
Based on the results, I found 3 urgent tickets..."
```

Benefits:
- Better reasoning
- Easier to debug
- More transparent to users

### Tree of Thoughts (ToT)

Explore multiple reasoning paths, backtrack if needed.

### Multi-Agent Systems

Multiple specialized agents collaborating:
- Research agent
- Writing agent
- Code agent

### Retrieval-Augmented Generation (RAG)

Give agents access to vector databases for knowledge retrieval.

## Common Pitfalls

### 1. Infinite Tool Loops

**Problem**: Agent keeps calling the same tool forever.

**Solution**: Track tool call history, detect loops.

### 2. Prompt Injection

**Problem**: User tricks agent into ignoring instructions.

**Solution**: Separate user input from system instructions.

### 3. Hallucinated Tool Calls

**Problem**: Model invents tools that don't exist.

**Solution**: Strict validation, clear tool documentation.

### 4. Context Window Overflow

**Problem**: Conversation gets too long for context window.

**Solution**:
- Summarization
- Rolling window
- Semantic compression

## Key Takeaways

1. **ReAct pattern** = Think → Act → Observe → Repeat
2. **Tools** = Agent's interface to the world (validate everything!)
3. **Threads** = Multi-turn conversation memory
4. **Stopping conditions** = Critical for safety
5. **Observability** = Log everything for debugging
6. **Security** = Validate, audit, limit access

## Further Reading

### Papers
- **ReAct**: [Paper](https://arxiv.org/abs/2210.03629) - Original ReAct pattern
- **Toolformer**: [Paper](https://arxiv.org/abs/2302.04761) - Teaching LLMs to use tools
- **Chain-of-Thought**: [Paper](https://arxiv.org/abs/2201.11903) - Reasoning in LLMs

### Resources
- [Anthropic Tool Use Guide](https://docs.anthropic.com/claude/docs/tool-use)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [LangChain Agents](https://python.langchain.com/docs/modules/agents/)

### Blog Posts
- [Building LLM Agents](https://lilianweng.github.io/posts/2023-06-23-agent/) by Lilian Weng
- [The Rise of Agentic AI](https://www.sequoiacap.com/article/ai-agents/) by Sequoia Capital

## Next Steps

To deepen your understanding:

1. **Modify the agent loop**: Try different prompting strategies
2. **Add new tools**: Implement your own custom tools
3. **Experiment with models**: Try different Claude models
4. **Add RAG**: Integrate a vector database
5. **Build multi-agent**: Create multiple specialized agents
6. **Production-ize**: Add auth, rate limiting, monitoring

The best way to learn is by **building**! 🚀

---

Questions? Check the code - it's heavily commented with learning in mind.
