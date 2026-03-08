# FastAPI Best Practices

Production-ready patterns and recommendations.

## Async/Await Patterns

### When to Use Async

**Use `async def` for:**
- Database operations (SQLModel, SQLAlchemy)
- External API calls (httpx, aiohttp)
- File I/O operations
- WebSocket connections
- Any I/O-bound operations

```python
# Good: Async for I/O operations
@app.get("/users/")
async def read_users(session: SessionDep):
    result = await session.execute(select(User))
    return result.scalars().all()

@app.get("/external-data/")
async def fetch_external_data():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
        return response.json()
```

### When to Use Sync

**Use regular `def` for:**
- CPU-bound operations
- Simple logic without I/O
- Synchronous libraries

```python
# Good: Sync for CPU-bound operations
@app.post("/calculate/")
def calculate_result(data: list[int]):
    # Heavy computation
    return {"result": sum(x ** 2 for x in data)}

# Good: Sync for simple operations
@app.get("/health")
def health_check():
    return {"status": "ok"}
```

### Avoid Blocking the Event Loop

```python
# Bad: Blocking operation in async function
@app.get("/bad/")
async def bad_endpoint():
    time.sleep(5)  # Blocks the entire event loop!
    return {"done": True}

# Good: Use asyncio.sleep
@app.get("/good/")
async def good_endpoint():
    await asyncio.sleep(5)  # Non-blocking
    return {"done": True}

# Good: Run blocking code in thread pool
import asyncio
from concurrent.futures import ThreadPoolExecutor

@app.get("/blocking/")
async def run_blocking_code():
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, blocking_function)
    return {"result": result}
```

## Code Organization

### Project Structure

```
app/
├── __init__.py
├── main.py              # FastAPI app, startup/shutdown
├── config.py            # Settings with pydantic-settings
├── database.py          # Database engine, session
├── models.py            # SQLModel table models
├── schemas.py           # Pydantic request/response schemas
├── dependencies.py      # Shared dependencies
├── routers/             # Route modules by domain
│   ├── __init__.py
│   ├── users.py
│   ├── items.py
│   └── teams.py
├── auth/                # Authentication logic
│   ├── __init__.py
│   ├── security.py      # Password hashing, JWT
│   └── dependencies.py  # Auth dependencies
├── services/            # Business logic
│   ├── __init__.py
│   ├── user_service.py
│   └── item_service.py
└── utils/               # Utility functions
    ├── __init__.py
    └── helpers.py
```

### Separation of Concerns

```python
# models.py - Database models
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str
    email: str
    hashed_password: str

# schemas.py - API schemas
class UserCreate(SQLModel):
    username: str
    email: str
    password: str

class UserPublic(SQLModel):
    id: int
    username: str
    email: str

class UserUpdate(SQLModel):
    email: str | None = None

# services/user_service.py - Business logic
async def create_user(user: UserCreate, session: AsyncSession) -> User:
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password)
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

# routers/users.py - Route handlers
@router.post("/users/", response_model=UserPublic)
async def create_user_endpoint(
    user: UserCreate,
    session: SessionDep
):
    return await create_user(user, session)
```

## Error Handling

### Consistent Error Responses

```python
# Custom exception classes
class ItemNotFoundError(Exception):
    def __init__(self, item_id: int):
        self.item_id = item_id

class InsufficientPermissionsError(Exception):
    pass

# Exception handlers
@app.exception_handler(ItemNotFoundError)
async def item_not_found_handler(request: Request, exc: ItemNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": f"Item {exc.item_id} not found"}
    )

@app.exception_handler(InsufficientPermissionsError)
async def permissions_handler(request: Request, exc: InsufficientPermissionsError):
    return JSONResponse(
        status_code=403,
        content={"detail": "Insufficient permissions"}
    )
```

### Graceful Database Error Handling

```python
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

@app.post("/users/", response_model=UserPublic)
async def create_user(user: UserCreate, session: SessionDep):
    try:
        db_user = User.model_validate(user)
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        return db_user
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=400,
            detail="User with this username or email already exists"
        )
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Database error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Database error occurred"
        )
```

## Performance Optimization

### Database Query Optimization

```python
# Bad: N+1 query problem
@app.get("/teams/")
async def read_teams(session: SessionDep):
    teams = await session.execute(select(Team))
    result = []
    for team in teams.scalars():
        # This triggers a separate query for each team!
        heroes = await session.execute(
            select(Hero).where(Hero.team_id == team.id)
        )
        result.append({"team": team, "heroes": heroes.scalars().all()})
    return result

# Good: Eager loading with selectinload
from sqlalchemy.orm import selectinload

@app.get("/teams/")
async def read_teams(session: SessionDep):
    statement = select(Team).options(selectinload(Team.heroes))
    result = await session.execute(statement)
    return result.scalars().all()
```

### Pagination

```python
from typing import Annotated
from fastapi import Query

class PaginationParams:
    def __init__(
        self,
        skip: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=100)] = 20
    ):
        self.skip = skip
        self.limit = limit

@app.get("/items/")
async def read_items(
    pagination: Annotated[PaginationParams, Depends()],
    session: SessionDep
):
    statement = select(Item).offset(pagination.skip).limit(pagination.limit)
    result = await session.execute(statement)
    items = result.scalars().all()

    # Get total count
    count_statement = select(func.count(Item.id))
    total = await session.execute(count_statement)

    return {
        "items": items,
        "total": total.scalar(),
        "skip": pagination.skip,
        "limit": pagination.limit
    }
```

### Caching

```python
from functools import lru_cache
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

# Simple in-memory cache
@lru_cache(maxsize=128)
def get_expensive_data(param: str):
    # Expensive computation
    return result

# Redis cache (requires fastapi-cache2)
@app.get("/cached-data/")
@cache(expire=60)  # Cache for 60 seconds
async def get_cached_data():
    return {"data": "expensive to compute"}
```

## Security Best Practices

### Input Validation

```python
from pydantic import BaseModel, Field, validator, EmailStr

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(..., min_length=8)

    @validator('password')
    def password_strength(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/limited/")
@limiter.limit("5/minute")
async def limited_endpoint(request: Request):
    return {"message": "This endpoint is rate limited"}
```

### SQL Injection Prevention

```python
# Good: Use ORM (SQLModel/SQLAlchemy)
@app.get("/users/search/")
async def search_users(name: str, session: SessionDep):
    statement = select(User).where(User.name.contains(name))
    result = await session.execute(statement)
    return result.scalars().all()

# Bad: Raw SQL with string formatting (NEVER DO THIS!)
@app.get("/users/search/")
async def search_users_bad(name: str, session: SessionDep):
    # VULNERABLE TO SQL INJECTION!
    query = f"SELECT * FROM users WHERE name LIKE '%{name}%'"
    result = await session.execute(query)
    return result.fetchall()
```

## API Design

### Consistent Response Format

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar('T')

class Response(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    message: str | None = None

@app.get("/items/{item_id}", response_model=Response[Item])
async def read_item(item_id: int, session: SessionDep):
    item = await session.get(Item, item_id)
    if not item:
        return Response(success=False, message="Item not found")
    return Response(success=True, data=item)
```

### API Versioning

```python
# URL versioning
v1_router = APIRouter(prefix="/api/v1")
v2_router = APIRouter(prefix="/api/v2")

@v1_router.get("/items/")
async def read_items_v1():
    return {"version": "v1"}

@v2_router.get("/items/")
async def read_items_v2():
    return {"version": "v2", "enhanced": True}

app.include_router(v1_router)
app.include_router(v2_router)
```

### Documentation

```python
from fastapi import FastAPI

app = FastAPI(
    title="My API",
    description="A comprehensive API for managing resources",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.post(
    "/items/",
    response_model=Item,
    status_code=201,
    summary="Create a new item",
    description="Create a new item with the provided data",
    response_description="The created item",
    tags=["items"]
)
async def create_item(item: ItemCreate):
    """
    Create a new item with all the information:

    - **name**: required, item name
    - **description**: optional, item description
    - **price**: required, item price (must be positive)
    """
    return item
```

## Configuration Management

### Environment-Based Settings

```python
from enum import Enum
from pydantic_settings import BaseSettings

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings(BaseSettings):
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    database_url: str
    secret_key: str

    # Environment-specific settings
    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION

    @property
    def cors_origins(self) -> list[str]:
        if self.is_production:
            return ["https://yourdomain.com"]
        return ["http://localhost:3000", "http://localhost:8000"]

    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }
```

## Logging

```python
import logging
from pythonjsonlogger import jsonlogger

# Structured logging
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("request_started", extra={
        "method": request.method,
        "path": request.url.path,
        "client": request.client.host
    })
    response = await call_next(request)
    logger.info("request_completed", extra={
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code
    })
    return response
```

## Testing Best Practices

### Test Fixtures

```python
# tests/conftest.py
import pytest
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

@pytest.fixture(name="session", scope="function")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
```

### Factory Pattern for Test Data

```python
# tests/factories.py
from app.models import User
from app.auth.security import get_password_hash

def create_test_user(session: Session, **kwargs) -> User:
    defaults = {
        "username": "testuser",
        "email": "test@example.com",
        "hashed_password": get_password_hash("testpassword")
    }
    defaults.update(kwargs)
    user = User(**defaults)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
```

## Deployment Best Practices

### Health Checks

```python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/health/ready")
async def readiness_check(session: SessionDep):
    try:
        await session.execute(select(1))
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Not ready")
```

### Graceful Shutdown

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application starting up")
    await create_db_and_tables()
    yield
    # Shutdown
    logger.info("Application shutting down")
    # Close database connections, cleanup resources

app = FastAPI(lifespan=lifespan)
```
