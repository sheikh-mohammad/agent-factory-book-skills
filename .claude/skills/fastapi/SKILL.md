---
name: fastapi
description: |
  Build FastAPI applications from hello world to production-ready APIs. Covers routing, request/response handling, dependency injection, Pydantic models, SQLModel database integration with Neon Serverless PostgreSQL, authentication (OAuth2/JWT), middleware, background tasks, testing, and deployment (Docker, cloud, traditional servers).
  This skill should be used when building REST APIs, real-time applications with WebSockets, data/ML APIs, microservices, or any Python web service using FastAPI. Triggers when users ask to create FastAPI projects, add endpoints, implement authentication, integrate databases, write tests, or deploy FastAPI applications.
---

# FastAPI Builder

Build FastAPI applications with embedded best practices from official documentation.

## What This Skill Does

- Creates FastAPI projects from scratch (hello world to production)
- Implements REST API endpoints with proper request/response handling
- Integrates SQLModel with Neon Serverless PostgreSQL
- Adds authentication (OAuth2, JWT, API keys)
- Implements WebSocket endpoints for real-time features
- Writes tests using pytest and TestClient
- Creates deployment configurations (Docker, cloud platforms, traditional servers)
- Applies async/await patterns correctly
- Handles errors and validation properly

## What This Skill Does NOT Do

- Deploy to production environments (provides configs only)
- Manage production databases (provides connection patterns)
- Handle frontend development (API-focused)
- Create GraphQL APIs (REST/WebSocket only)

---

## Before Implementation

Gather context to ensure successful implementation:

| Source | Gather |
|--------|--------|
| **Codebase** | Existing FastAPI structure, models, routes, database setup, auth patterns |
| **Conversation** | User's specific requirements, endpoints needed, data models, auth requirements |
| **Skill References** | FastAPI patterns from `references/` (routing, database, auth, testing, deployment) |
| **User Guidelines** | Project conventions, code style, deployment targets |

Ensure all required context is gathered before implementing.
Only ask user for THEIR specific requirements (domain expertise is in this skill).

---

## Project Clarifications

Ask about project-specific requirements (not FastAPI knowledge):

### 1. Project Type
- **New project**: Start from scratch with project structure
- **Add to existing**: Integrate with existing codebase
- **Specific feature**: Add endpoints, auth, database, etc.

### 2. API Scope
What endpoints/features are needed?
- CRUD operations for specific resources
- Authentication/authorization
- File uploads/downloads
- WebSocket connections
- Background tasks
- Third-party integrations

### 3. Data Models
What data structures are needed?
- Resource schemas (users, products, orders, etc.)
- Relationships between models
- Validation rules

### 4. Database Requirements
- **New database**: Set up SQLModel + Neon connection
- **Existing database**: Connect to existing schema
- **No database**: API only (external services, proxies)

### 5. Authentication Needs
- **None**: Public API
- **API Keys**: Simple token-based
- **OAuth2 + JWT**: Full user authentication
- **External**: Auth0, Firebase, etc.

### 6. Deployment Target
- **Docker**: Container-based deployment
- **Cloud**: AWS, GCP, Azure specifics
- **Traditional**: VPS with systemd/supervisor
- **Development only**: Local setup

---

## Implementation Workflow

### Phase 1: Project Setup

**For new projects:**
1. Create project structure (see `references/project-structure.md`)
2. Initialize dependencies (`requirements.txt` or `pyproject.toml`)
3. Set up configuration management (environment variables)
4. Create main application file with FastAPI instance

**For existing projects:**
1. Analyze current structure
2. Identify integration points
3. Ensure dependency compatibility

### Phase 2: Core Implementation

**Follow this order:**

1. **Models** (if database needed)
   - Define SQLModel classes (see `references/database-integration.md`)
   - Set up relationships
   - Create Pydantic schemas for API

2. **Database Connection** (if database needed)
   - Configure Neon Serverless PostgreSQL connection
   - Set up async engine and session dependency
   - Create database initialization

3. **Routes & Endpoints**
   - Implement path operations (see `references/fastapi-core.md`)
   - Use proper HTTP methods (GET, POST, PUT, PATCH, DELETE)
   - Add request/response models
   - Implement dependency injection

4. **Authentication** (if needed)
   - Set up OAuth2 with password flow (see `references/authentication.md`)
   - Implement JWT token generation/validation
   - Create protected route dependencies
   - Add user management endpoints

5. **Error Handling**
   - Add custom exception handlers
   - Implement validation error responses
   - Add logging

6. **Background Tasks** (if needed)
   - Implement async background tasks
   - Add task queue if complex processing needed

### Phase 3: Testing

1. Write tests using pytest and TestClient (see `references/testing.md`)
2. Test all endpoints (success and error cases)
3. Test authentication flows
4. Test database operations

### Phase 4: Deployment Preparation

1. Create deployment configuration (see `references/deployment.md`)
2. Set up environment variable management
3. Configure production settings (workers, logging, CORS)
4. Create Docker configuration if needed
5. Document deployment steps

---

## Implementation Standards

### Code Organization

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app instance
│   ├── config.py            # Settings with pydantic-settings
│   ├── database.py          # Database connection & session
│   ├── models.py            # SQLModel table models
│   ├── schemas.py           # Pydantic request/response models
│   ├── dependencies.py      # Reusable dependencies
│   ├── routers/             # Route modules
│   │   ├── __init__.py
│   │   ├── users.py
│   │   └── items.py
│   └── auth/                # Authentication logic
│       ├── __init__.py
│       ├── security.py
│       └── dependencies.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_*.py
├── requirements.txt
├── .env.example
├── Dockerfile
└── README.md
```

### Async/Await Rules

- Use `async def` for endpoints that perform I/O (database, external APIs)
- Use regular `def` for CPU-bound operations or simple logic
- Always `await` async database operations
- Use `asyncio` for concurrent operations

### Database Patterns

- One session per request (dependency injection)
- Always close sessions (use `yield` in dependencies)
- Use transactions for multi-step operations
- Handle database errors gracefully

### Security Checklist

- [ ] Passwords hashed (never stored plain text)
- [ ] JWT secrets in environment variables
- [ ] CORS configured for production
- [ ] Input validation on all endpoints
- [ ] SQL injection prevented (use ORM, not raw SQL)
- [ ] Rate limiting considered for production
- [ ] HTTPS enforced in production

---

## Quality Checklist

Before completing implementation:

### Functionality
- [ ] All requested endpoints implemented
- [ ] Request/response models defined with Pydantic
- [ ] Database operations work correctly
- [ ] Authentication works (if required)
- [ ] Error handling implemented

### Code Quality
- [ ] Type hints used throughout
- [ ] Dependency injection used properly
- [ ] No code duplication
- [ ] Async/await used correctly
- [ ] Environment variables for configuration

### Testing
- [ ] Tests written for all endpoints
- [ ] Tests pass successfully
- [ ] Edge cases covered
- [ ] Authentication tests (if applicable)

### Documentation
- [ ] OpenAPI docs auto-generated (available at `/docs`)
- [ ] Environment variables documented
- [ ] Deployment instructions provided
- [ ] README updated

### Deployment Ready
- [ ] Dependencies listed in requirements.txt
- [ ] Environment variables in .env.example
- [ ] Deployment configuration created
- [ ] Production settings configured

---

## Quick Reference

### Common Patterns

**Basic endpoint:**
```python
@app.get("/items/{item_id}")
async def read_item(item_id: int) -> Item:
    return {"item_id": item_id}
```

**With database:**
```python
@app.get("/items/{item_id}")
async def read_item(item_id: int, session: SessionDep) -> Item:
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
```

**Protected endpoint:**
```python
@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
```

**See `references/` for complete patterns and examples.**

---

## Reference Files

| File | Content |
|------|---------|
| `references/fastapi-core.md` | Routing, request/response, dependency injection, validation |
| `references/database-integration.md` | SQLModel patterns, Neon PostgreSQL setup, async sessions |
| `references/authentication.md` | OAuth2, JWT, password hashing, protected routes |
| `references/testing.md` | pytest setup, TestClient, fixtures, async tests |
| `references/deployment.md` | Docker, cloud platforms, production configuration |
| `references/best-practices.md` | Async patterns, error handling, performance, security |
| `references/anti-patterns.md` | Common mistakes and how to avoid them |

## Template Files

| File | Purpose |
|------|---------|
| `assets/templates/hello-world/` | Minimal FastAPI starter |
| `assets/templates/crud-api/` | Full CRUD API with database |
| `assets/templates/auth-api/` | API with authentication |
