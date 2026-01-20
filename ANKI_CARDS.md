# Anki Cards: Agentic Systems

Format: Question | Answer (separated by pipe for easy import into Anki)

---

## Core Concepts

**Front:** What is an Agentic System?
**Back:** An AI system that can:<br>1. Reason about what to do next<br>2. Act by using tools<br>3. Observe the results<br>4. Iterate until completing the task<br><br>Unlike chatbots that just respond, agents are goal-oriented and break down complex tasks into steps.

---

**Front:** What does ReAct stand for and what is it?
**Back:** ReAct = <b>Re</b>asoning + <b>Act</b>ing<br><br>The most popular agent pattern:<br>1. Think (reason about what to do)<br>2. Act (use a tool OR give final answer)<br>3. Observe (see tool result)<br>4. Repeat until done

---

**Front:** What is a Tool in agentic systems?
**Back:** An action the agent can perform to interact with the world:<br>- Database queries<br>- API calls<br>- File operations<br>- Computations<br><br>Tools are the agent's "hands" - without them, agents can only talk.

---

**Front:** What are the 3 required stopping conditions for an agent loop?
**Back:** 1. <b>Final answer</b>: Model decides it's done<br>2. <b>Max iterations</b>: Safety limit reached<br>3. <b>Error</b>: Something went wrong<br><br>Without stopping conditions, agents can loop forever!

---

**Front:** Why is max_iterations critical in agent loops?
**Back:** Prevents:<br>- Infinite loops<br>- Wasted API credits<br>- Hanging requests<br>- Resource exhaustion<br><br>Typical values: 5-20 depending on task complexity<br><br><b>Rule: ALWAYS set max_iterations!</b>

---

**Front:** What is a Thread in agentic systems?
**Back:** A conversation container that holds multi-turn dialogue history.<br><br>Enables:<br>- Multi-turn conversations<br>- Context retention<br>- Reference to earlier messages<br><br>Think: Thread = One conversation with memory

---

**Front:** What is a Run in agentic systems?
**Back:** A single execution of the agent loop (one API call).<br><br>Contains:<br>- User message<br>- Assistant response<br>- Number of iterations<br>- Status (success/error/max_iterations)<br>- All tool calls made during execution

---

**Front:** What is a Trace in agentic systems?
**Back:** Complete record of an agent's execution including:<br>- All steps taken<br>- All tool calls with inputs/outputs<br>- Errors encountered<br>- Final answer<br>- Performance metrics (latency, etc.)<br><br>Critical for debugging and observability!

---

**Front:** What is a Tool Call?
**Back:** When the model decides to use a tool instead of answering directly.<br><br>Includes:<br>- Tool name<br>- Tool input parameters<br>- Tool output/result<br>- Latency measurement<br><br>Must be validated and logged!

---

**Front:** What is an Observation in ReAct?
**Back:** The result of a tool call, fed back into the agent's context.<br><br><b>Critical:</b> Tool results MUST be added to conversation history so the agent can use them for next reasoning step.<br><br>Without observations, agent can't learn from actions!

---

## Tool Design

**Front:** What are the 4 required components of every tool?
**Back:** 1. <b>Name</b>: What the tool is called<br>2. <b>Description</b>: What it does (helps model choose)<br>3. <b>Input Schema</b>: Parameters with validation (Pydantic)<br>4. <b>Function</b>: The actual implementation<br><br>Plus: Error handling, timeouts, logging!

---

**Front:** Why must you ALWAYS validate tool inputs?
**Back:** Because agents can send:<br>- Invalid data types<br>- Missing required fields<br>- SQL injection attempts<br>- Malicious payloads<br><br><b>Rule: Never trust agent input!</b><br><br>Use Pydantic schemas for validation.

---

**Front:** What makes a good tool description?
**Back:** <b>Bad:</b> "query_db" → Unclear what it queries<br><br><b>Good:</b> "Query customer database by email or plan type" → Clear and specific<br><br><b>Why:</b> Model chooses tools based on descriptions!<br><br><b>Include:</b> What it does, when to use it, what parameters it needs

---

**Front:** What should tool execution return?
**Back:** Structured result with:<br>- <b>success</b>: bool<br>- <b>data</b>: The actual result (if success)<br>- <b>error</b>: Error message (if failed)<br>- <b>latency</b>: Execution time<br><br>This enables proper error handling and observability.

---

## Anti-Patterns

**Front:** Anti-Pattern: No Max Iterations
**Back:** <b>Problem:</b> Agent loops forever, wastes money<br><br><b>Fix:</b> Always set max_iterations<br><br><b>Default:</b> 10<br><b>Range:</b> 5-20 depending on complexity

---

**Front:** Anti-Pattern: No Input Validation
**Back:** <b>Problem:</b> SQL injection, crashes, security holes<br><br><b>Fix:</b> Use Pydantic schemas for every tool input<br><br>Validate:<br>- Data types<br>- Required fields<br>- Value ranges<br>- Format (email, URL, etc.)

---

**Front:** Anti-Pattern: No Error Handling
**Back:** <b>Problem:</b> One tool failure crashes entire agent<br><br><b>Fix:</b> Wrap tool execution in try/except<br><br>Return ToolResult with success=False and error message so agent can adapt.

---

**Front:** Anti-Pattern: No Observability
**Back:** <b>Problem:</b> Can't debug what agent did<br><br><b>Fix:</b> Log and persist:<br>- Every tool call<br>- Inputs and outputs<br>- Errors<br>- Latencies<br>- Model responses<br><br>Store in database for analysis!

---

**Front:** Anti-Pattern: Trusting Agent Output Blindly
**Back:** <b>Problem:</b> Agent might hallucinate tool calls, send invalid inputs<br><br><b>Fix:</b> Validate everything at tool boundary:<br>- Tool exists?<br>- Input schema valid?<br>- Parameters in range?<br>- Permissions OK?

---

**Front:** Anti-Pattern: Ignoring Context Window Limits
**Back:** <b>Problem:</b> Conversations get too long, requests fail<br><br><b>Fix:</b> Implement:<br>- Summarization (compress old messages)<br>- Rolling window (keep recent N messages)<br>- Semantic compression (extract key facts)

---

**Front:** Anti-Pattern: No Timeouts on Tools
**Back:** <b>Problem:</b> One slow tool hangs entire request<br><br><b>Fix:</b> Set timeouts on all tool executions<br><br><b>Default:</b> 30 seconds<br><b>Adjust:</b> Based on expected tool latency

---

**Front:** Anti-Pattern: Poor Tool Descriptions
**Back:** <b>Problem:</b> Model can't choose right tool<br><br><b>Fix:</b> Write clear, specific descriptions:<br>- What it does<br>- When to use it<br>- Example use cases<br>- Parameter explanations

---

**Front:** Anti-Pattern: No Rate Limiting
**Back:** <b>Problem:</b> Agent spams tools/APIs, gets banned<br><br><b>Fix:</b> Implement:<br>- Per-user rate limits<br>- Per-tool rate limits<br>- Exponential backoff<br>- Request queuing

---

**Front:** Anti-Pattern: Mixing User Input and System Prompts
**Back:** <b>Problem:</b> Prompt injection attacks<br><br><b>Fix:</b> Separate:<br>- System instructions (trusted)<br>- User messages (untrusted)<br><br>Never concatenate directly!

---

## Best Practices

**Front:** What are the 5 critical security practices for agents?
**Back:** 1. <b>Input validation</b> (Pydantic)<br>2. <b>Least privilege</b> (minimal tool access)<br>3. <b>Rate limiting</b> (prevent abuse)<br>4. <b>Audit logs</b> (persist all tool calls)<br>5. <b>Sandboxing</b> (isolate tool execution)<br><br>Security is critical - agents access sensitive systems!

---

**Front:** What should you always log for observability?
**Back:** For every tool call:<br>- Tool name<br>- Input parameters<br>- Output/result<br>- Error messages<br>- Latency (ms)<br>- Timestamp<br>- User/thread context<br><br>Store in database for debugging and analysis!

---

**Front:** What's the difference between streaming and non-streaming?
**Back:** <b>Non-streaming:</b> Wait for full response (30+ seconds)<br><br><b>Streaming (SSE):</b> See agent "think" in real-time:<br>- "I'll query customers..."<br>- "Found 3 customers"<br>- "Checking tickets..."<br>- "Here's the result"<br><br>Much better UX!

---

**Front:** When should you use MockModel vs real model?
**Back:** <b>MockModel (local testing):</b><br>- Development<br>- Testing<br>- CI/CD pipelines<br>- No API key needed<br>- Free and fast<br><br><b>Real Model:</b><br>- Production<br>- E2E testing<br>- User acceptance testing

---

**Front:** How do you handle context window overflow?
**Back:** <b>Problem:</b> Conversation too long for LLM context<br><br><b>Solutions:</b><br>1. <b>Summarization</b>: Compress old messages<br>2. <b>Rolling window</b>: Keep only recent N messages<br>3. <b>Semantic compression</b>: Extract key facts<br>4. <b>RAG</b>: Store in vector DB, retrieve relevant parts

---

## Architecture

**Front:** What is the core agent loop pseudocode?
**Back:** ```python<br>while not done:<br>&nbsp;&nbsp;response = model.generate(context)<br>&nbsp;&nbsp;if response.is_final_answer:<br>&nbsp;&nbsp;&nbsp;&nbsp;return answer<br>&nbsp;&nbsp;else:<br>&nbsp;&nbsp;&nbsp;&nbsp;result = execute_tool(response.tool_call)<br>&nbsp;&nbsp;&nbsp;&nbsp;context.append(result)  # Feed back!<br>```<br><br><b>Key:</b> Tool results fed back into context!

---

**Front:** What database tables are needed for agent persistence?
**Back:** <b>threads</b>: Conversation containers<br>↓<br><b>messages</b>: User/assistant messages<br>↓<br><b>runs</b>: Each agent execution<br>↓<br><b>tool_calls</b>: Individual tool executions<br><br>Plus: Your domain tables (customers, tickets, etc.)

---

**Front:** What are the 4 FastAPI endpoints for an agent system?
**Back:** 1. <b>POST /chat</b>: Main endpoint (non-streaming)<br>2. <b>POST /chat/stream</b>: Streaming with SSE<br>3. <b>GET /threads/{id}</b>: Get conversation history<br>4. <b>GET /runs/{id}</b>: Get execution trace<br><br>Plus: GET /healthz for monitoring

---

## Mental Models

**Front:** Mental Model: Agent as Junior Developer
**Back:** Think of agents like junior devs:<br>- Need clear instructions (descriptions)<br>- Make mistakes (validation needed)<br>- Need feedback (tool results)<br>- Have limits (max iterations)<br>- Need supervision (error handling)<br><br>Don't expect perfection!

---

**Front:** Mental Model: ReAct as Scientific Method
**Back:** 1. <b>Hypothesis</b> → Model thinks what to do<br>2. <b>Experiment</b> → Execute tool<br>3. <b>Observation</b> → See result<br>4. <b>Iterate</b> → Use result for next hypothesis<br><br>Just like science: test, observe, learn, repeat!

---

**Front:** Mental Model: Tools as Agent's Hands
**Back:** <b>Without tools:</b> Agent can only talk<br><b>With tools:</b> Agent can DO things<br><br><b>Remember:</b> More tools ≠ better!<br><br>Keep tools focused and well-described.<br><br>Each tool = one capability agent can perform.

---

**Front:** Mental Model: Context Window as Working Memory
**Back:** Like human working memory:<br>- Limited space<br>- Older memories fade (need summarization)<br>- Important facts must persist (database)<br>- Can't hold everything (need retrieval)<br><br>Manage it carefully!

---

## Performance

**Front:** 4 ways to optimize agent latency?
**Back:** 1. <b>Parallel tool calls</b>: When independent<br>2. <b>Streaming</b>: Better perceived performance<br>3. <b>Caching</b>: Repeated queries<br>4. <b>Smaller models</b>: For simple tasks<br><br>Measure everything to find bottlenecks!

---

**Front:** 5 ways to optimize agent costs?
**Back:** 1. <b>Track tokens</b> per request<br>2. <b>Use MockModel</b> for development<br>3. <b>Cache responses</b> when possible<br>4. <b>Set budgets</b> per user/session<br>5. <b>Cheaper models</b> for tool selection<br><br>Costs add up fast with multi-step agents!

---

## Debugging

**Front:** Agent not using tools - what to check?
**Back:** 1. Are tools in tool list?<br>2. Are descriptions clear and specific?<br>3. Check prompt engineering<br>4. Look at model's reasoning in trace<br>5. Is tool schema correct?<br>6. Test with MockModel first

---

**Front:** Agent loops forever - what to check?
**Back:** 1. Is max_iterations set?<br>2. Are tool results formatted correctly?<br>3. Is agent receiving tool results?<br>4. Check stopping condition logic<br>5. Look at trace to find loop pattern<br>6. Are errors being handled?

---

**Front:** Tools failing - what to check?
**Back:** 1. Check input validation errors (Pydantic)<br>2. Look at error logs<br>3. Verify database connections<br>4. Check API credentials<br>5. Test tool independently<br>6. Check timeouts<br>7. Verify permissions

---

## Quick Commands

**Front:** 3 commands to verify code quality?
**Back:** 1. `make fmt` → Format with Ruff<br>2. `make lint` → Lint with Ruff<br>3. `make typecheck` → Type check with Pyright<br><br>Or: `make check` runs all three plus tests!

---

**Front:** Command to run tests with coverage?
**Back:** `python -m pytest --cov=agent_chat --cov-report=html`<br><br>Or simply: `make test`<br><br>Opens HTML report showing what's covered.

---

**Front:** Command to test the chat endpoint?
**Back:** ```bash<br>curl -X POST http://localhost:8000/chat \<br>&nbsp;&nbsp;-H "Content-Type: application/json" \<br>&nbsp;&nbsp;-d '{"message": "Show me customers"}'<br>```

---

## 10 One-Sentence Reminders

**Front:** Reminder #1: Input Validation
**Back:** Always validate tool inputs - agents can send anything!

---

**Front:** Reminder #2: Max Iterations
**Back:** Always set max_iterations - prevents infinite loops.

---

**Front:** Reminder #3: Feedback Loop
**Back:** Always feed tool results back - that's how learning happens!

---

**Front:** Reminder #4: Observability
**Back:** Always log everything - you'll need it for debugging.

---

**Front:** Reminder #5: Error Handling
**Back:** Always handle errors - tools fail, be ready.

---

**Front:** Reminder #6: Tool Descriptions
**Back:** Clear descriptions matter - model chooses based on them.

---

**Front:** Reminder #7: Development Testing
**Back:** Test with MockModel first - save API credits.

---

**Front:** Reminder #8: User Experience
**Back:** Streaming improves UX - users see progress.

---

**Front:** Reminder #9: Context Limits
**Back:** Context has limits - summarize or truncate.

---

**Front:** Reminder #10: Security
**Back:** Security is critical - validate, audit, limit access.

---

## Technology Stack

**Front:** Why Python 3.14 for agents?
**Back:** <b>New in 3.14:</b><br>- Free-threading (better multi-core)<br>- Experimental JIT compiler (faster)<br>- Deferred annotations (better type hints)<br><br>Latest stable with best performance!

---

**Front:** Why FastAPI for agent APIs?
**Back:** - High-performance async<br>- Built-in validation (Pydantic)<br>- Automatic OpenAPI docs<br>- SSE support for streaming<br>- Type hints everywhere<br><br>Best Python web framework for APIs!

---

**Front:** Why Ruff for linting?
**Back:** Written in Rust:<br>- 10-100x faster than Flake8/Black<br>- Replaces multiple tools<br>- Auto-fixes issues<br>- Modern Python support<br><br>State-of-the-art as of 2026!

---

**Front:** Why SQLAlchemy 2.0?
**Back:** - Modern ORM with type safety<br>- Async support<br>- Mapped columns with types<br>- Great PostgreSQL support<br>- Production-ready<br><br>Best Python ORM!

---

**Front:** Why Anthropic Claude for agents?
**Back:** - Leading edge AI models<br>- Excellent tool use support<br>- Long context windows<br>- Strong reasoning<br>- JSON mode for structured output<br><br>Best for agentic workflows!

---

## Common Mistakes

**Front:** Mistake: Not reading files before editing
**Back:** <b>Wrong:</b> Edit file you haven't seen<br><br><b>Right:</b> Read file first to understand context<br><br>Prevents breaking existing code!

---

**Front:** Mistake: Testing only the happy path
**Back:** Also test:<br>- Error cases<br>- Invalid inputs<br>- Edge cases<br>- Timeouts<br>- Network failures<br><br>80% coverage minimum!

---

**Front:** Mistake: Not persisting tool calls
**Back:** <b>Problem:</b> Can't debug or audit<br><br><b>Fix:</b> Persist to database:<br>- Tool name<br>- Inputs/outputs<br>- Errors<br>- Latency<br>- Timestamp<br><br>Critical for production!

---

## Production Readiness

**Front:** What are the 7 production readiness checks?
**Back:** 1. Input validation (Pydantic)<br>2. Error handling (try/except)<br>3. Timeouts (all tools)<br>4. Logging (all actions)<br>5. Rate limiting (per user)<br>6. Monitoring (metrics)<br>7. Testing (80%+ coverage)<br><br>Don't skip any!

---

**Front:** What metrics should you monitor in production?
**Back:** - Requests per minute<br>- Average response time<br>- Error rate<br>- Token usage<br>- Cost per request<br>- Tool execution latency<br>- Max iterations hit rate<br>- Cache hit rate

---

## End of Cards

Total: 75+ Anki cards covering all core concepts!

---

# How to Import into Anki

1. **Save this file** or copy the cards
2. **In Anki**: File → Import → Choose text file
3. **Format**: Each card has "Front:" and "Back:" clearly marked
4. **Manual entry** or use Anki card creation
5. **Deck name**: "Agentic Systems"

Or use a tool like:
- **Markdown to Anki** converter
- **AnkiConnect** API
- Copy-paste into Anki directly
