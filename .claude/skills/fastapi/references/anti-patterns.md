# FastAPI Anti-Patterns

Common mistakes and how to avoid them.

## Async/Await Mistakes

### Blocking the Event Loop

```python
# ❌ Bad: Blocking operation in async function
@app.get("/bad/")
async def bad_endpoint():
    time.sleep(5)  # Blocks entire event loop!
    return {"done": True}

# ✅ Good: Use asyncio.sleep
@app.get("/good/")
async def good_endpoint():
    await asyncio.sleep(5)
    return {"done": True}
```

### Forgetting to Await

```python
# ❌ Bad: Not awaiting async function
@app.get("/users/")
async def read_users(session: SessionDep):
    result = session.execute(select(User))  # Missing await!
    return result.scalars().all()

# ✅ Good: Await async operations
@app.get("/users/")
async def read_users(session: SessionDep):
    result = await session.execute(select(User))
    return result.scalars().all()
```

### Using Async When Not Needed

```python
# ❌ Bad: Unnecessary async for CPU-bound work
@app.post("/calculate/")
async def calculate(data: list[int]):
    # No I/O operations, async adds overhead
    return {"result": sum(x ** 2 for x in data)}

# ✅ Good: Use sync for CPU-bound operations
@app.post("/calculate/")
def calculate(data: list[int]):
    return {"result": sum(x ** 2 for x in data)}
```

## Database Mistakes

### Not Closing Sessions

```python
# ❌ Bad: Session not properly closed
def get_session_bad():
    session = Session(engine)
    return session  # Session never closed!

# ✅ Good: Use yield to ensure cleanup
def get_session():
    with Session(engine) as session:
        yield session
```

### N+1 Query Problem

```python
# ❌ Bad: Separate query for each relationship
@app.get("/teams/")
async def read_teams(session: SessionDep):
    teams = await session.execute(select(Team))
    for team in teams.scalars():
        # New query for each team!
        heroes = await session.execute(
            select(Hero).where(Hero.team_id == team.id)
        )
    return teams

# ✅ Good: Eager load relationships
from sqlalchemy.orm import selectinload

@app.get("/teams/")
async def read_teams(session: SessionDep):
    statement = select(Team).options(selectinload(Team.heroes))
    result = await session.execute(statement)
    return result.scalars().all()
```

### Not Using Transactions

```python
# ❌ Bad: No transaction for multi-step operation
@app.post("/transfer/")
async def transfer_money(from_id: int, to_id: int, amount: float, session: SessionDep):
    from_account = await session.get(Account, from_id)
    from_account.balance -= amount
    await session.commit()  # What if next line fails?

    to_account = await session.get(Account, to_id)
    to_account.balance += amount
    await session.commit()

# ✅ Good: Use transaction
@app.post("/transfer/")
async def transfer_money(from_id: int, to_id: int, amount: float, session: SessionDep):
    try:
        from_account = await session.get(Account, from_id)
        to_account = await session.get(Account, to_id)

        from_account.balance -= amount
        to_account.balance += amount

        await session.commit()  # Both or neither
    except Exception:
        await session.rollback()
        raise
```

### Storing Passwords in Plain Text

```python
# ❌ Bad: Plain text passwords
class User(SQLModel, table=True):
    username: str
    password: str  # NEVER store plain text!

@app.post("/register/")
async def register(username: str, password: str, session: SessionDep):
    user = User(username=username, password=password)
    session.add(user)
    await session.commit()

# ✅ Good: Hash passwords
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(SQLModel, table=True):
    username: str
    hashed_password: str

@app.post("/register/")
async def register(username: str, password: str, session: SessionDep):
    user = User(
        username=username,
        hashed_password=pwd_context.hash(password)
    )
    session.add(user)
    await session.commit()
```

## Security Mistakes

### Hardcoded Secrets

```python
# ❌ Bad: Secrets in code
SECRET_KEY = "my-secret-key-123"
DATABASE_URL = "postgresql://user:password@localhost/db"

# ✅ Good: Use environment variables
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str
    database_url: str

    model_config = {"env_file": ".env"}

settings = Settings()
```

### SQL Injection Vulnerability

```python
# ❌ Bad: String formatting with user input
@app.get("/users/search/")
async def search_users(name: str, session: SessionDep):
    query = f"SELECT * FROM users WHERE name = '{name}'"  # VULNERABLE!
    result = await session.execute(query)
    return result.fetchall()

# ✅ Good: Use ORM or parameterized queries
@app.get("/users/search/")
async def search_users(name: str, session: SessionDep):
    statement = select(User).where(User.name == name)
    result = await session.execute(statement)
    return result.scalars().all()
```

### Overly Permissive CORS

```python
# ❌ Bad: Allow all origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dangerous in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Good: Restrict origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### Exposing Sensitive Information in Errors

```python
# ❌ Bad: Leaking implementation details
@app.get("/users/{user_id}")
async def read_user(user_id: int, session: SessionDep):
    try:
        user = await session.get(User, user_id)
        return user
    except Exception as e:
        # Exposes database structure, file paths, etc.
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Good: Generic error messages
@app.get("/users/{user_id}")
async def read_user(user_id: int, session: SessionDep):
    try:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

## API Design Mistakes

### Inconsistent Response Formats

```python
# ❌ Bad: Different response formats
@app.get("/users/{user_id}")
async def read_user(user_id: int):
    if user_id == 1:
        return {"user": {"id": 1, "name": "John"}}
    else:
        return {"id": 2, "name": "Jane"}  # Different structure!

# ✅ Good: Consistent response models
class UserResponse(BaseModel):
    id: int
    name: str

@app.get("/users/{user_id}", response_model=UserResponse)
async def read_user(user_id: int):
    return UserResponse(id=user_id, name="John")
```

### Not Using Response Models

```python
# ❌ Bad: No response model, returns everything
@app.get("/users/{user_id}")
async def read_user(user_id: int, session: SessionDep):
    user = await session.get(User, user_id)
    return user  # Returns hashed_password, internal fields!

# ✅ Good: Use response model to filter fields
class UserPublic(BaseModel):
    id: int
    username: str
    email: str

@app.get("/users/{user_id}", response_model=UserPublic)
async def read_user(user_id: int, session: SessionDep):
    user = await session.get(User, user_id)
    return user  # Only UserPublic fields returned
```

### Missing Pagination

```python
# ❌ Bad: Return all records (can be millions!)
@app.get("/items/")
async def read_items(session: SessionDep):
    result = await session.execute(select(Item))
    return result.scalars().all()  # Could return 1M+ items!

# ✅ Good: Always paginate
@app.get("/items/")
async def read_items(
    session: SessionDep,
    skip: int = 0,
    limit: int = Query(default=20, le=100)
):
    statement = select(Item).offset(skip).limit(limit)
    result = await session.execute(statement)
    return result.scalars().all()
```

## Dependency Injection Mistakes

### Creating Dependencies Inside Endpoints

```python
# ❌ Bad: Creating session inside endpoint
@app.get("/users/")
async def read_users():
    session = Session(engine)  # Manual session management
    try:
        result = await session.execute(select(User))
        return result.scalars().all()
    finally:
        session.close()

# ✅ Good: Use dependency injection
@app.get("/users/")
async def read_users(session: SessionDep):
    result = await session.execute(select(User))
    return result.scalars().all()
```

### Not Reusing Dependencies

```python
# ❌ Bad: Duplicate dependency logic
@app.get("/users/me")
async def read_user_me(token: str = Header(...)):
    # Duplicate token validation logic
    payload = jwt.decode(token, SECRET_KEY)
    username = payload.get("sub")
    # ...

@app.put("/users/me")
async def update_user_me(token: str = Header(...)):
    # Same logic duplicated!
    payload = jwt.decode(token, SECRET_KEY)
    username = payload.get("sub")
    # ...

# ✅ Good: Create reusable dependency
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = jwt.decode(token, SECRET_KEY)
    username = payload.get("sub")
    # ... get user from database
    return user

@app.get("/users/me")
async def read_user_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.put("/users/me")
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    # ...
```

## Testing Mistakes

### Not Using Test Database

```python
# ❌ Bad: Testing against production database
def test_create_user():
    client = TestClient(app)  # Uses production DB!
    response = client.post("/users/", json={"username": "test"})
    assert response.status_code == 201

# ✅ Good: Use test database with dependency override
@pytest.fixture
def client(session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
```

### Not Testing Error Cases

```python
# ❌ Bad: Only testing happy path
def test_create_user(client):
    response = client.post("/users/", json={"username": "test"})
    assert response.status_code == 201

# ✅ Good: Test error cases too
def test_create_user_success(client):
    response = client.post("/users/", json={"username": "test"})
    assert response.status_code == 201

def test_create_user_duplicate(client):
    client.post("/users/", json={"username": "test"})
    response = client.post("/users/", json={"username": "test"})
    assert response.status_code == 400

def test_create_user_invalid_data(client):
    response = client.post("/users/", json={"username": ""})
    assert response.status_code == 422
```

## Deployment Mistakes

### Running Single Worker in Production

```bash
# ❌ Bad: Single worker (no concurrency)
uvicorn app.main:app --host 0.0.0.0 --port 8000

# ✅ Good: Multiple workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Not Setting Up Health Checks

```python
# ❌ Bad: No health check endpoint
# Container orchestrators can't verify app health

# ✅ Good: Add health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/health/ready")
async def readiness_check(session: SessionDep):
    try:
        await session.execute(select(1))
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Not ready")
```

### Debug Mode in Production

```python
# ❌ Bad: Debug mode in production
app = FastAPI(debug=True)  # Exposes stack traces!

# ✅ Good: Environment-based configuration
from app.config import settings

app = FastAPI(debug=settings.debug)  # False in production
```

## Performance Mistakes

### Not Using Connection Pooling

```python
# ❌ Bad: New connection for each request
@app.get("/users/")
async def read_users():
    engine = create_engine(DATABASE_URL)  # New connection!
    with Session(engine) as session:
        result = await session.execute(select(User))
        return result.scalars().all()

# ✅ Good: Reuse engine with connection pool
# database.py
engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)

# routes.py
@app.get("/users/")
async def read_users(session: SessionDep):
    result = await session.execute(select(User))
    return result.scalars().all()
```

### Loading Too Much Data

```python
# ❌ Bad: Loading all fields when only need few
@app.get("/users/names/")
async def read_user_names(session: SessionDep):
    result = await session.execute(select(User))
    users = result.scalars().all()
    return [{"name": user.name} for user in users]

# ✅ Good: Select only needed columns
@app.get("/users/names/")
async def read_user_names(session: SessionDep):
    statement = select(User.id, User.name)
    result = await session.execute(statement)
    return [{"id": id, "name": name} for id, name in result]
```
