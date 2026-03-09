---
name: chatkit-server
description: |
  Build conversational AI backends with OpenAI ChatKit from hello world to production systems.
  Covers FastAPI backend setup, Vite frontend integration, agent configuration, tool integration,
  vector stores, streaming responses, error handling, and deployment across 17+ industry domains
  (manufacturing, productivity, enterprise knowledge, sales, marketing, support, product, finance,
  accounting, legal, data analysis, healthcare, HR, architecture, ERP, education, consulting).
  This skill should be used when building conversational AI applications, chatbots, AI assistants,
  knowledge bases, customer support systems, or any interactive AI backend using OpenAI's ChatKit framework.
---

# ChatKit Server Skill

Build production-grade conversational AI backends using OpenAI's ChatKit framework.

## What This Skill Does

- Creates ChatKit projects from scratch (FastAPI backend + Vite frontend)
- Implements industry-specific conversational AI patterns (17+ domains)
- Configures agents, tools, and vector stores
- Handles streaming responses and error management
- Guides production deployment and scaling

## What This Skill Does NOT Do

- Build non-conversational applications (use FastAPI skill instead)
- Create OpenAI API integrations without ChatKit framework (use claude-api skill)
- Handle frontend-only implementations (ChatKit requires backend)

---

## Before Implementation

Gather context to ensure successful implementation:

| Source | Gather |
|--------|--------|
| **Codebase** | Existing ChatKit projects, API patterns, environment setup |
| **Conversation** | User's industry domain, specific use case, integration requirements |
| **Skill References** | Architecture patterns from `references/`, industry-specific examples |
| **User Guidelines** | Team conventions, deployment environment, security requirements |

Ensure all required context is gathered before implementing.
Only ask user for THEIR specific requirements (domain expertise is in this skill).

---

## Implementation Workflow

### 1. Clarify Requirements

Ask user about THEIR specific context:

#### Required Clarifications

| Clarification | Purpose |
|---------------|---------|
| **Industry Domain** | Which of 17+ domains? (manufacturing, sales, support, etc.) |
| **Use Case** | Specific problem to solve (e.g., "automate customer inquiries") |
| **Deployment Target** | Local dev, Docker, cloud platform (AWS, Azure, GCP) |

#### Optional Clarifications

| Clarification | Purpose | When to Ask |
|---------------|---------|-------------|
| **Data Sources** | Existing knowledge bases, APIs, databases to integrate | If use case involves knowledge retrieval or external data |
| **Existing Infrastructure** | Current tech stack, authentication system, monitoring | If integrating with existing systems |

**Note**: Avoid asking too many questions in a single message. Start with required clarifications, then ask optional ones based on responses.

### 2. Choose Architecture Pattern

Based on use case, select appropriate ChatKit architecture:

| Pattern | When to Use | Reference |
|---------|-------------|-----------|
| **Simple Agent** | Single-purpose bot, no external data | `references/architecture-patterns.md#simple` |
| **Knowledge Assistant** | Document search, RAG, citations | `references/architecture-patterns.md#knowledge` |
| **Tool-Augmented Agent** | API calls, database queries, actions | `references/architecture-patterns.md#tools` |
| **Multi-Agent System** | Complex workflows, handoffs, specialization | `references/architecture-patterns.md#multi-agent` |
| **Hybrid System** | Combines knowledge + tools + multiple agents | `references/architecture-patterns.md#hybrid` |

### 3. Initialize Project

Use initialization script or manual setup:

```bash
# Option A: Use script (recommended)
python scripts/init-project.py --name <project-name> --pattern <architecture-pattern>

# Option B: Manual setup with templates
mkdir <project-name> && cd <project-name>
# Copy templates from assets/templates/:
# - Dockerfile.backend
# - Dockerfile.frontend
# - docker-compose.yml
# - requirements.txt
# - package.json
# - nginx.conf
# - .env.example
```

### 4. Configure Backend

Set up FastAPI backend with ChatKit:

| Component | Configuration |
|-----------|---------------|
| **Environment** | OPENAI_API_KEY, domain keys, vector store IDs |
| **Dependencies** | Install via uv: `uv pip install -r requirements.txt` |
| **Agent Setup** | Configure in `app/main.py` - see `references/chatkit-api.md` |
| **Tools** | Implement custom tools - see `references/tool-patterns.md` |
| **Vector Stores** | Set up for knowledge retrieval - see `references/vector-stores.md` |

### 5. Configure Frontend

Set up Vite frontend:

| Component | Configuration |
|-----------|---------------|
| **Environment** | VITE_CHATKIT_API_DOMAIN_KEY |
| **API Client** | Connect to FastAPI backend |
| **UI Components** | Chat interface, streaming display |

### 6. Implement Industry-Specific Logic

Apply domain patterns from `references/industry-patterns.md`:

- Manufacturing: Equipment monitoring, maintenance scheduling
- Sales: Prospect research, deal preparation
- Support: Issue triage, response drafting
- Finance: Financial analysis, model building
- Healthcare: Clinical documentation, coding
- [See full list in references]

### 7. Test and Validate

| Test Type | What to Verify |
|-----------|----------------|
| **Unit Tests** | Individual tool functions, data processing |
| **Integration Tests** | Agent responses, tool execution, API calls |
| **End-to-End Tests** | Full conversation flows, error handling |
| **Load Tests** | Concurrent users, streaming performance |

### 8. Deploy to Production

Follow deployment guide in `references/deployment.md`:

- Local: `npm start` (dev mode)
- Docker: Multi-stage build with uvicorn + nginx
- Cloud: Platform-specific deployment (AWS ECS, Azure Container Apps, GCP Cloud Run)

---

## Decision Trees

### When to Use Vector Stores

```
Does use case require knowledge retrieval?
├─ YES: Documents, policies, historical data
│  └─ Create vector store → Upload documents → Configure in agent
└─ NO: Simple Q&A, API-only interactions
   └─ Skip vector store setup
```

### When to Create Custom Tools

```
Does agent need to take actions or query external systems?
├─ YES: Database queries, API calls, file operations
│  ├─ Simple operations → Implement as function tools
│  └─ Complex workflows → Create tool classes with state
└─ NO: Pure conversation, knowledge retrieval only
   └─ Use built-in ChatKit capabilities
```

### When to Use Multi-Agent Architecture

```
Does use case involve multiple specialized domains?
├─ YES: Different expertise areas, handoffs, escalation
│  └─ Implement multi-agent with handoff logic
└─ NO: Single domain, straightforward workflow
   └─ Use single agent architecture
```

---

## Error Handling

| Error Type | Handling Strategy |
|------------|-------------------|
| **OpenAI API Errors** | Retry with exponential backoff, fallback responses |
| **Tool Execution Errors** | Catch exceptions, return error to agent, log for debugging |
| **Vector Store Errors** | Fallback to non-RAG responses, alert monitoring |
| **Streaming Errors** | Graceful degradation, buffer management |
| **Rate Limits** | Queue requests, implement backpressure |

See `references/error-handling.md` for detailed patterns.

---

## Security Considerations

| Concern | Mitigation |
|---------|------------|
| **API Key Exposure** | Environment variables, never commit to git |
| **Input Validation** | Sanitize user inputs, validate tool parameters |
| **Output Filtering** | Prevent sensitive data leakage, PII redaction |
| **Authentication** | Implement auth middleware, domain key validation |
| **Rate Limiting** | Per-user limits, abuse prevention |

See `references/security.md` for complete security checklist.

---

## Production Checklist

Before deploying to production:

- [ ] Environment variables configured (OPENAI_API_KEY, domain keys)
- [ ] Vector stores created and populated (if using knowledge retrieval)
- [ ] Custom tools implemented and tested
- [ ] Error handling implemented for all failure modes
- [ ] Logging and monitoring configured
- [ ] Rate limiting and authentication enabled
- [ ] Load testing completed
- [ ] Security review passed
- [ ] Documentation updated (API endpoints, tool descriptions)
- [ ] Deployment pipeline configured (CI/CD)

---

## Must Avoid: Common Anti-Patterns

| Anti-Pattern | Why It's Wrong | Correct Approach |
|--------------|----------------|------------------|
| **Hardcoding API keys** | Security risk, keys exposed in git | Use environment variables, secrets manager |
| **No error handling** | Crashes on API failures | Implement retry logic, fallback responses |
| **Blocking operations** | Poor UX, timeouts | Use streaming, async operations |
| **Single agent for everything** | Poor scalability, mixed concerns | Use multi-agent for complex domains |
| **No input validation** | Security vulnerabilities, injection attacks | Sanitize inputs, validate tool parameters |
| **Storing sensitive data in logs** | PII exposure, compliance violations | Redact PII, use structured logging |
| **No rate limiting** | API quota exhaustion, abuse | Implement per-user rate limits |
| **Skipping vector store for knowledge** | Poor responses, hallucinations | Use vector stores for document-based knowledge |
| **No authentication** | Unauthorized access, security breach | Implement API key or JWT authentication |
| **Ignoring CORS in production** | Security risk | Restrict CORS to specific domains |

---

## Good vs Bad Examples

### Example 1: Environment Configuration

❌ **Bad**: Hardcoded credentials
```python
OPENAI_API_KEY = "sk-proj-abc123..."
DATABASE_URL = "postgresql://user:pass@localhost/db"
```

✅ **Good**: Environment variables
```python
import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
```

### Example 2: Error Handling

❌ **Bad**: No error handling
```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages
)
return response.choices[0].message.content
```

✅ **Good**: Comprehensive error handling
```python
try:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )
    return response.choices[0].message.content
except RateLimitError:
    return "Service busy, please try again"
except Exception as e:
    logger.error(f"Error: {str(e)}")
    return "An error occurred"
```

### Example 3: Tool Implementation

❌ **Bad**: No validation
```python
def send_email(to: str, subject: str, body: str):
    email_service.send(to, subject, body)
    return {"success": True}
```

✅ **Good**: Input validation
```python
def send_email(to: str, subject: str, body: str):
    if not validate_email(to):
        return {"error": "Invalid email address"}
    if not subject or len(subject) > 200:
        return {"error": "Subject must be 1-200 characters"}

    try:
        email_service.send(to, subject, body)
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}
```

---

## Version Awareness

**Current Framework**: OpenAI ChatKit (as of March 2026)

**Staying Updated**:
- Check OpenAI platform for latest API changes: https://platform.openai.com/docs
- Review ChatKit examples repository for new patterns
- Monitor OpenAI changelog for breaking changes
- Test with latest OpenAI Python SDK versions

**When Patterns Change**:
1. Review `references/chatkit-api.md` for outdated patterns
2. Update architecture patterns if new capabilities added
3. Test existing implementations with new SDK versions
4. Update security practices for new vulnerabilities

**Compatibility Notes**:
- This skill uses OpenAI Assistants API (beta) - check for GA changes
- Vector stores API may evolve - verify current endpoints
- Tool calling format stable but monitor for improvements

---

## Common Patterns

### Streaming Responses

```python
# Backend: Enable streaming in agent configuration
agent = Agent(
    model="gpt-4",
    stream=True
)

# Frontend: Handle streaming events
eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)
    // Update UI incrementally
}
```

### Tool Integration

```python
# Define custom tool
def query_database(query: str) -> str:
    """Query internal database for information."""
    # Implementation
    return results

# Register with agent
agent.add_tool(query_database)
```

### Vector Store Setup

```python
# Create vector store (one-time setup)
vector_store = client.beta.vector_stores.create(
    name="Knowledge Base"
)

# Upload documents
client.beta.vector_stores.file_batches.upload_and_poll(
    vector_store_id=vector_store.id,
    files=[open("doc.pdf", "rb")]
)

# Configure agent to use vector store
agent = Agent(
    vector_store_ids=[vector_store.id]
)
```

---

## Quick Start Examples

### Hello World (Simple Agent)

```bash
# 1. Set environment
export OPENAI_API_KEY="sk-proj-..."
export VITE_CHATKIT_API_DOMAIN_KEY="your-key"

# 2. Initialize project
python scripts/init-project.py --name hello-chatkit --pattern simple

# 3. Start services
cd hello-chatkit && npm start

# Backend: http://localhost:8000
# Frontend: http://localhost:5170
```

### Knowledge Assistant

```bash
# 1. Create vector store at platform.openai.com/storage/vector_stores
# 2. Upload documents and copy store ID

# 3. Set environment
export OPENAI_API_KEY="sk-proj-..."
export KNOWLEDGE_VECTOR_STORE_ID="vs_..."
export VITE_CHATKIT_API_DOMAIN_KEY="your-key"

# 4. Initialize project
python scripts/init-project.py --name knowledge-bot --pattern knowledge

# 5. Start services
cd knowledge-bot && npm start
```

### Tool-Augmented Agent (Customer Support)

```bash
# 1. Set environment
export OPENAI_API_KEY="sk-proj-..."
export VITE_CHATKIT_API_DOMAIN_KEY="your-key"

# 2. Initialize project
python scripts/init-project.py --name support-bot --pattern tools

# 3. Implement custom tools in app/tools/
# 4. Start services
cd support-bot && npm start
```

---

## Reference Files

| File | Purpose |
|------|---------|
| `references/architecture-patterns.md` | 5 ChatKit architectures with examples |
| `references/chatkit-api.md` | Core API patterns from official docs |
| `references/industry-patterns.md` | 17+ industry-specific implementations |
| `references/tool-patterns.md` | Custom tool development guide |
| `references/vector-stores.md` | Knowledge retrieval setup |
| `references/deployment.md` | Production deployment strategies |
| `references/error-handling.md` | Error handling patterns |
| `references/security.md` | Security best practices |
| `references/testing.md` | Testing strategies and examples |
| `references/troubleshooting.md` | Common issues and solutions |
| `references/versioning-strategy.md` | Skill maintenance and update process |

## Template Files

| File | Purpose |
|------|---------|
| `assets/templates/Dockerfile.backend` | Production-ready backend Docker image |
| `assets/templates/Dockerfile.frontend` | Multi-stage frontend build with nginx |
| `assets/templates/docker-compose.yml` | Complete stack orchestration |
| `assets/templates/requirements.txt` | Python dependencies with versions |
| `assets/templates/package.json` | Node.js dependencies and scripts |
| `assets/templates/nginx.conf` | Nginx configuration with security headers |
| `assets/templates/.env.example` | Environment variable template |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Module not found" | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| "API key invalid" | Verify OPENAI_API_KEY format: `sk-proj-...` |
| "Vector store not found" | Check KNOWLEDGE_VECTOR_STORE_ID matches platform.openai.com |
| "Port already in use" | Change port in package.json scripts |
| "Streaming not working" | Verify frontend EventSource connection to backend |

For detailed troubleshooting, see `references/troubleshooting.md`.
