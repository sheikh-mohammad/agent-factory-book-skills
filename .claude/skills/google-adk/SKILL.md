---
name: google-adk
description: |
  Build reliable AI agents with Google ADK (Agent Development Kit) and Gemini from hello world to production systems.
  Covers agent creation, tools integration (function tools, OpenAPI, MCP), multi-agent coordination, authentication, state management, error handling, testing, and deployment (local, FastAPI, Google Cloud).
  This skill should be used when building conversational agents, task automation, API integrations, multi-agent systems, or deploying AI agents to production using Google's Agent Development Kit with Gemini models.
---

# Google ADK Agent Development

Build production-grade AI agents with Google ADK and Gemini.

## Before Implementation

Gather context to ensure successful implementation:

| Source | Gather |
|--------|--------|
| **Codebase** | Existing agent structure, tools, authentication patterns, deployment configuration |
| **Conversation** | User's specific requirements, agent purpose, tools needed, deployment target |
| **Skill References** | ADK patterns from `references/` (API docs, authentication, tools, deployment) |
| **User Guidelines** | Project conventions, security requirements, infrastructure constraints |

Ensure all required context is gathered before implementing.
Only ask user for THEIR specific requirements (domain expertise is in this skill).

---

## Required Clarifications

Ask users about their specific requirements:

1. **Agent Purpose**: What should the agent do? (e.g., customer service, data analysis, task automation)
2. **Deployment Target**: Where will this run?
   - Local development only
   - Self-hosted (FastAPI/Docker)
   - Google Cloud Run
3. **Authentication Needs**: Will the agent access external APIs?
   - No authentication needed
   - API key authentication
   - OAuth2 (client credentials or user delegation)
   - Google Cloud service accounts
4. **Complexity Level**: What's the scope?
   - Single agent with basic tools
   - Multi-agent system with coordination
   - Production system with full observability

**Note**: Only ask what's relevant to their use case. Don't ask all questions if scope is clear.

## Optional Clarifications

Ask if relevant to the specific use case:

- **Existing Infrastructure**: Do you have existing agents or services to integrate with?
- **Performance Requirements**: Expected request volume or latency requirements?
- **Monitoring Needs**: Specific observability or logging requirements?
- **Team Experience**: Team's familiarity with Python async, Gemini API, or GCP?

---

## Version Compatibility

This skill covers **Google ADK Python 1.x** (latest as of 2026). Key compatibility notes:
- Requires Python 3.11+
- Compatible with Gemini 2.5 models (flash, pro)
- Works with both Google AI Studio and Vertex AI backends
- For latest features, check [ADK releases](https://github.com/google/adk-python/releases)

---

## What This Skill Does

- Creates agents from hello world to production systems
- Integrates tools (Python functions, OpenAPI, MCP, Google Cloud)
- Implements authentication and security patterns
- Builds multi-agent systems with A2A coordination
- Manages state, memory, and sessions
- Handles errors and implements recovery strategies
- Deploys to local, FastAPI, or Google Cloud environments
- Provides monitoring, debugging, and production patterns

## What This Skill Does NOT Do

- Train or fine-tune Gemini models (uses pre-trained models)
- Replace domain-specific business logic (agents call your tools)
- Manage infrastructure provisioning (focuses on agent code)
- Handle non-ADK agent frameworks (specific to Google ADK)

## Expected Outputs

This skill produces:
- **Python code** for agent definitions, tools, and runners
- **Configuration files** (.env, requirements.txt, Dockerfile)
- **Deployment scripts** (Cloud Run deployment commands)
- **Testing code** (unit tests, integration tests)

All code is production-ready with error handling, authentication, and best practices.

---

## Common Mistakes to Avoid

- ❌ Using InMemoryRunner in production (use Runner with managed services)
- ❌ Hardcoding API keys in code (use environment variables or Secret Manager)
- ❌ Skipping error handling in tools (always handle exceptions)
- ❌ Not validating tool inputs (validate before processing)
- ❌ Using `gemini-2.5-pro` when `gemini-2.5-flash` suffices (cost/speed)
- ❌ Forgetting to add docstrings to tools (required for agent to understand)
- ❌ Not testing agents before deployment (use debug mode)
- ❌ Storing sensitive data in session state without encryption
- ❌ Ignoring rate limits (implement exponential backoff)
- ❌ Not setting timeouts on external API calls (can hang indefinitely)

---

## Frequently Asked Questions

**Q: ADK vs LangChain - which should I use?**
A: Use ADK for Gemini-native agents with Google Cloud integration. Use LangChain for multi-model flexibility.

**Q: When to use Vertex AI vs Google AI Studio?**
A: AI Studio for development/prototyping (simpler, faster). Vertex AI for production (managed, scalable, enterprise features).

**Q: Can I use ADK with non-Google models?**
A: No, ADK is designed specifically for Gemini models. For multi-model support, consider LangChain or custom implementations.

**Q: How do I handle long-running operations?**
A: Use async tools, implement timeouts, consider background tasks, or use streaming for real-time feedback.

---

## Quick Start Examples

### Example 1: Hello World (30 seconds)
```python
from google.adk import Agent
from google.adk.runners import InMemoryRunner

agent = Agent(name="hello", model="gemini-2.5-flash", instruction="Be helpful.")
runner = InMemoryRunner(agent=agent, app_name="demo")
await runner.run_debug("Hello!")
```

### Example 2: Weather Agent with Tool (2 minutes)
```python
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"{city}: Sunny, 72°F"

agent = Agent(name="weather", model="gemini-2.5-flash",
              instruction="Help with weather using get_weather tool.",
              tools=[get_weather])
runner = InMemoryRunner(agent=agent, app_name="weather")
await runner.run_debug("What's the weather in Tokyo?")
```

### Example 3: Production Agent (5 minutes)
```python
from google.adk import Agent, Runner
from google.adk.sessions import VertexAiSessionService

agent = Agent(name="prod", model="gemini-2.5-flash",
              instruction="Production assistant.", tools=[...])
runner = Runner(app_name="prod", agent=agent,
    session_service=VertexAiSessionService(project_id="...", location="us-central1"))
```

---

## Core Workflow

### 1. Setup and Configuration

**Install ADK:**
```bash
pip install google-adk
# or with uv
uv pip install google-adk
```

**Configure authentication** (choose one):
```bash
# Option 1: Google AI Studio (development)
export GOOGLE_API_KEY=your_api_key

# Option 2: Vertex AI (production)
export GOOGLE_GENAI_USE_VERTEXAI=1
export GOOGLE_CLOUD_PROJECT=your_project_id
export GOOGLE_CLOUD_LOCATION=us-central1
```

See `references/setup-and-config.md` for detailed setup instructions.

### 2. Create Your First Agent

```python
from google.adk import Agent
from google.adk.runners import InMemoryRunner

agent = Agent(
    name="assistant",
    model="gemini-2.5-flash",
    instruction="You are a helpful assistant.",
)

runner = InMemoryRunner(agent=agent, app_name="hello_world")
await runner.run_debug("Hello! What can you do?")
```

**CLI:** `adk run agent.py` or `adk web .`

### 3. Add Tools

**Function Tools:** Python functions with docstrings
```python
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Weather in {city}: Sunny, 72°F"

agent = Agent(name="weather_assistant", model="gemini-2.5-flash", tools=[get_weather])
```

**OpenAPI Tools:** Auto-generate from API specs
```python
from google.adk.tools import OpenApiToolset
api_tools = OpenApiToolset(spec_url="https://api.example.com/openapi.json")
```

**MCP Tools:** Model Context Protocol integrations
```python
from google.adk.tools import McpToolset
from mcp import StdioServerParameters
mcp_tools = McpToolset(connection_params=StdioServerParameters(
    command="npx", args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]))
```

See `references/tools-integration.md` for details.

### 4. State Management and Memory

**Session State:** Use `ToolContext` to access/modify state
```python
def add_to_cart(item: str, quantity: int, tool_context: ToolContext) -> str:
    cart = tool_context.state.get("cart", [])
    cart.append({"item": item, "quantity": quantity})
    tool_context.state["cart"] = cart
    return f"Added {quantity}x {item}"
```

**Long-term Memory:** Configure memory service on Runner
```python
from google.adk import Runner
from google.adk.memory import InMemoryMemoryService

runner = Runner(app_name="app", agent=agent, memory_service=InMemoryMemoryService())
```

See `references/state-and-memory.md`.

### 5. Multi-Agent Systems

Create specialized agents and coordinate with `sub_agents`:
```python
from google.adk.agents import LlmAgent

researcher = LlmAgent(name="researcher", model="gemini-2.5-flash",
                      instruction="Research topics.", tools=[search_tool])
writer = LlmAgent(name="writer", model="gemini-2.5-flash",
                  instruction="Write content.")
coordinator = LlmAgent(name="coordinator", model="gemini-2.5-flash",
                       instruction="Coordinate tasks.", sub_agents=[researcher, writer])
```

See `references/multi-agent.md`.

### 6. Authentication and Security

Wrap tools with authentication:
```python
from google.adk.tools import AuthenticatedFunctionTool
from google.adk.tools.authentication import OAuth2CredentialExchanger, ApiKeyCredentialExchanger

# OAuth2
oauth_tool = AuthenticatedFunctionTool(function=api_call,
    credential_exchanger=OAuth2CredentialExchanger(
        client_id="...", client_secret="...", token_url="..."))

# API Key
api_tool = AuthenticatedFunctionTool(function=api_call,
    credential_exchanger=ApiKeyCredentialExchanger(api_key="...", header_name="X-API-Key"))
```

See `references/authentication.md`.

### 7. Error Handling and Recovery

Use callbacks for error handling:
```python
async def handle_model_error(ctx, request, error):
    logger.error(f"Model error: {error}")
    return LlmResponse(content=types.Content(role="model",
        parts=[types.Part(text="Error occurred. Please try again.")]))

agent = Agent(name="resilient", model="gemini-2.5-flash",
              on_model_error_callback=handle_model_error)
```

**Recovery workflow:** Detect → Analyze → Retry → Escalate

See `references/error-handling.md`.

### 8. Testing and Debugging

Use `run_debug` for quick testing:
```python
await runner.run_debug("Query", verbose=True)  # Show tool calls
events = await runner.run_debug("Query", quiet=True)  # Programmatic
await runner.run_debug(["Query 1", "Query 2"])  # Multiple queries
await runner.run_debug("Query", user_id="alice", session_id="test")  # Persist context
```

See `references/testing-debugging.md`.

### 9. Deployment

**Local:** `adk run agent.py` or `adk web ./agents`

**FastAPI:**
```python
from google.adk.cli.fast_api import get_fast_api_app
app = get_fast_api_app(agent_dir="./agents")
```

**Cloud Run:**
```bash
adk deploy cloud_run --project=PROJECT --region=us-central1 --service_name=NAME ./agent_dir
```

**Production Runner:**
```python
from google.adk import Runner
from google.adk.sessions import VertexAiSessionService

runner = Runner(app_name="prod", agent=agent,
    session_service=VertexAiSessionService(project_id="...", location="us-central1"))
```

See `references/deployment.md`.

---

## Progressive Implementation Path

### Level 1: Hello World
- Single agent with basic instruction
- No tools, simple Q&A
- InMemoryRunner for testing
- CLI execution

### Level 2: Tool Integration
- Add function tools for specific capabilities
- Implement tool error handling
- Use session state for context
- Web UI for debugging

### Level 3: Production Features
- Authentication for tool access
- Error recovery strategies
- Structured logging and monitoring
- Environment-based configuration

### Level 4: Advanced Patterns
- Multi-agent coordination
- Long-term memory integration
- Streaming responses
- Custom callbacks for observability

### Level 5: Production Deployment
- FastAPI or Cloud Run deployment
- Managed services (Vertex AI sessions/memory)
- Monitoring and alerting
- CI/CD integration

---

## Key Decisions

| Decision | Options | Guidance | Example Use Case |
|----------|---------|----------|------------------|
| **Model Backend** | Google AI Studio vs Vertex AI | AI Studio for dev/prototyping, Vertex AI for production | Prototype: AI Studio; Enterprise: Vertex AI |
| **Model Selection** | gemini-2.5-flash vs pro | Flash for speed/cost, Pro for complex reasoning | Customer service: Flash; Legal analysis: Pro |
| **Runner Type** | InMemoryRunner vs Runner | InMemory for testing, Runner with services for production | Local dev: InMemory; Production: Runner |
| **Session Storage** | InMemory vs PostgreSQL vs Vertex AI | InMemory for dev, PostgreSQL for self-hosted, Vertex AI for GCP | Dev: InMemory; Self-hosted: PostgreSQL; GCP: Vertex AI |
| **Memory Service** | InMemory vs Vertex AI RAG | InMemory for simple cases, Vertex AI RAG for production | Simple bot: InMemory; Knowledge base: Vertex AI RAG |
| **Tool Type** | Function vs OpenAPI vs MCP | Function for custom logic, OpenAPI for REST APIs, MCP for protocols | Custom: Function; External API: OpenAPI; Filesystem: MCP |
| **Deployment** | Local vs FastAPI vs Cloud Run | Local for dev, FastAPI for self-hosted, Cloud Run for managed | Dev: Local; On-prem: FastAPI; Cloud: Cloud Run |
| **Authentication** | API Key vs OAuth2 vs Service Account | API Key for simple, OAuth2 for user delegation, SA for GCP | Internal: API Key; User data: OAuth2; GCP: Service Account |

---

## Production Checklist

Before deploying to production:

**Security & Authentication:**
- [ ] Authentication configured for all external tool access
- [ ] Secrets managed securely (Secret Manager, not .env)
- [ ] Input validation on all tool parameters
- [ ] API keys rotated and not hardcoded

**Reliability & Error Handling:**
- [ ] Error handling and recovery strategies implemented
- [ ] Timeouts set on all external API calls
- [ ] Rate limiting and exponential backoff implemented
- [ ] Circuit breakers for failing services

**Infrastructure & Deployment:**
- [ ] Session and memory services use managed storage (not InMemory)
- [ ] Environment variables externalized (not hardcoded)
- [ ] Health check endpoints added
- [ ] Deployment automation configured (CI/CD)
- [ ] Rollback strategy defined and tested

**Observability:**
- [ ] Logging configured (structured logging for Cloud Logging)
- [ ] Monitoring and alerting set up
- [ ] Performance metrics tracked (latency, token usage)

**Testing & Documentation:**
- [ ] Testing coverage for critical paths (unit + integration)
- [ ] Load testing completed
- [ ] Documentation for operations team
- [ ] Runbooks for common issues

---

## Common Patterns

### Pattern: Authenticated API Integration
Use OpenAPI tools with authentication for secure API access.
See `references/authentication.md#openapi-auth`

### Pattern: Multi-Agent Workflow
Coordinator agent delegates to specialized sub-agents.
See `references/multi-agent.md#hierarchical-teams`

### Pattern: Error Recovery
Detect errors, analyze context, retry with corrections, escalate if needed.
See `references/error-handling.md#recovery-workflow`

### Pattern: Stateful Conversations
Use ToolContext to maintain state across tool calls within a session.
See `references/state-and-memory.md#session-state`

### Pattern: Production Deployment
Use Runner with Vertex AI services for managed infrastructure.
See `references/deployment.md#production-runner`

---

## Reference Documentation

| File | Content |
|------|---------|
| `references/setup-and-config.md` | Installation, authentication, environment configuration |
| `references/core-concepts.md` | Agent, Runner, tools, sessions, memory fundamentals |
| `references/tools-integration.md` | Function tools, OpenAPI, MCP, Google Cloud tools |
| `references/authentication.md` | OAuth2, API keys, service accounts, security patterns |
| `references/state-and-memory.md` | Session state, long-term memory, context management |
| `references/multi-agent.md` | Agent teams, A2A coordination, workflow patterns |
| `references/error-handling.md` | Error recovery, callbacks, debugging strategies |
| `references/testing-debugging.md` | Debug mode, testing patterns, troubleshooting |
| `references/deployment.md` | Local, FastAPI, Cloud Run, production patterns |
| `references/api-reference.md` | Complete API documentation and examples |

---

## Troubleshooting Quick Reference

| Issue | Solution | Reference |
|-------|----------|-----------|
| Tool not called | Check docstring, make instruction explicit | testing-debugging.md |
| Tool errors | Add error handling, validate inputs | error-handling.md |
| State not persisting | Use same user_id/session_id | state-and-memory.md |
| Slow responses | Use gemini-2.5-flash, optimize tools | testing-debugging.md |
| Auth failures | Verify credentials, check token expiry | authentication.md |
| Deployment issues | Check env vars, increase timeout | deployment.md |

---

## Quick Reference

**Create agent:**
```python
agent = Agent(name="...", model="gemini-2.5-flash", instruction="...", tools=[...])
```

**Run locally:**
```bash
adk web ./agents
```

**Deploy to Cloud Run:**
```bash
adk deploy cloud_run --project=... --region=... --service_name=...
```

**Debug with verbose output:**
```python
await runner.run_debug("Query", verbose=True)
```

**Add authentication:**
```python
AuthenticatedFunctionTool(function=..., credential_exchanger=...)
```

---

## Official Documentation

- [Google ADK Documentation](https://github.com/google/adk-docs)
- [ADK Python Repository](https://github.com/google/adk-python)
- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
