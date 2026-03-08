# Testing FastAPI Applications

Testing patterns with pytest, TestClient, and async tests.

## Setup

```bash
pip install pytest httpx pytest-asyncio
```

```python
# pyproject.toml or pytest.ini
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

## TestClient Basics

### Simple Tests

```python
# tests/test_main.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_create_item():
    response = client.post(
        "/items/",
        json={"name": "Test Item", "price": 10.5}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["price"] == 10.5
    assert "id" in data
```

### Testing Path Parameters

```python
def test_read_item():
    response = client.get("/items/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1

def test_read_item_not_found():
    response = client.get("/items/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"
```

### Testing Query Parameters

```python
def test_read_items_with_pagination():
    response = client.get("/items/?skip=0&limit=10")
    assert response.status_code == 200
    items = response.json()
    assert len(items) <= 10

def test_read_items_with_filter():
    response = client.get("/items/?q=test")
    assert response.status_code == 200
```

## Database Testing

### Test Database Setup

```python
# tests/conftest.py
import pytest
from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_session

# In-memory SQLite for tests
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
```

### Testing CRUD Operations

```python
# tests/test_heroes.py
def test_create_hero(client: TestClient):
    response = client.post(
        "/heroes/",
        json={
            "name": "Deadpool",
            "secret_name": "Wade Wilson",
            "age": 35
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Deadpool"
    assert "id" in data

def test_read_heroes(client: TestClient, session: Session):
    # Create test data
    hero = Hero(name="Spider-Man", secret_name="Peter Parker", age=23)
    session.add(hero)
    session.commit()

    # Test endpoint
    response = client.get("/heroes/")
    assert response.status_code == 200
    heroes = response.json()
    assert len(heroes) >= 1

def test_update_hero(client: TestClient, session: Session):
    # Create hero
    hero = Hero(name="Iron Man", secret_name="Tony Stark", age=45)
    session.add(hero)
    session.commit()
    session.refresh(hero)

    # Update hero
    response = client.patch(
        f"/heroes/{hero.id}",
        json={"age": 46}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["age"] == 46

def test_delete_hero(client: TestClient, session: Session):
    # Create hero
    hero = Hero(name="Thor", secret_name="Thor Odinson", age=1500)
    session.add(hero)
    session.commit()
    session.refresh(hero)

    # Delete hero
    response = client.delete(f"/heroes/{hero.id}")
    assert response.status_code == 200

    # Verify deletion
    response = client.get(f"/heroes/{hero.id}")
    assert response.status_code == 404
```

## Async Testing

### Async Test Setup

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient

@pytest.fixture
async def async_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session

@pytest.fixture
async def async_client(async_session: AsyncSession):
    async def get_session_override():
        yield async_session

    app.dependency_overrides[get_session] = get_session_override

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
```

### Async Tests

```python
import pytest

@pytest.mark.asyncio
async def test_create_hero_async(async_client: AsyncClient):
    response = await async_client.post(
        "/heroes/",
        json={"name": "Captain America", "secret_name": "Steve Rogers", "age": 100}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Captain America"

@pytest.mark.asyncio
async def test_read_heroes_async(async_client: AsyncClient):
    response = await async_client.get("/heroes/")
    assert response.status_code == 200
```

## Authentication Testing

### Test Fixtures for Auth

```python
# tests/conftest.py
from app.auth.security import get_password_hash

@pytest.fixture
def test_user(session: Session):
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword")
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@pytest.fixture
def auth_client(client: TestClient, test_user: User):
    # Login and get token
    response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpassword"}
    )
    token = response.json()["access_token"]

    # Add token to client headers
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {token}"
    }
    return client
```

### Testing Authentication

```python
def test_login_success(client: TestClient, test_user: User):
    response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client: TestClient, test_user: User):
    response = client.post(
        "/token",
        data={"username": "testuser", "password": "wrongpassword"}
    )
    assert response.status_code == 401

def test_login_nonexistent_user(client: TestClient):
    response = client.post(
        "/token",
        data={"username": "nonexistent", "password": "password"}
    )
    assert response.status_code == 401
```

### Testing Protected Routes

```python
def test_read_users_me_authenticated(auth_client: TestClient):
    response = auth_client.get("/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"

def test_read_users_me_unauthenticated(client: TestClient):
    response = client.get("/users/me")
    assert response.status_code == 401

def test_read_users_me_invalid_token(client: TestClient):
    client.headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/users/me")
    assert response.status_code == 401
```

## Mocking External Dependencies

### Mocking External APIs

```python
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
@patch("app.services.external_api.fetch_data")
async def test_endpoint_with_external_api(
    mock_fetch: AsyncMock,
    async_client: AsyncClient
):
    # Mock the external API response
    mock_fetch.return_value = {"data": "mocked"}

    response = await async_client.get("/data")
    assert response.status_code == 200
    assert response.json() == {"data": "mocked"}
    mock_fetch.assert_called_once()
```

### Mocking Background Tasks

```python
from unittest.mock import MagicMock

def test_endpoint_with_background_task(client: TestClient):
    with patch("app.tasks.send_email") as mock_send_email:
        response = client.post(
            "/send-notification/",
            json={"email": "test@example.com", "message": "Hello"}
        )
        assert response.status_code == 200
        # Background task is queued but not executed in tests
```

## Testing Validation

```python
def test_create_item_invalid_data(client: TestClient):
    response = client.post(
        "/items/",
        json={"name": ""}  # Empty name should fail validation
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(error["loc"] == ["body", "name"] for error in errors)

def test_create_item_missing_required_field(client: TestClient):
    response = client.post(
        "/items/",
        json={"price": 10.5}  # Missing name
    )
    assert response.status_code == 422
```

## Testing Error Handling

```python
def test_internal_server_error(client: TestClient):
    with patch("app.services.process_data", side_effect=Exception("Error")):
        response = client.post("/process/", json={"data": [1, 2, 3]})
        assert response.status_code == 500

def test_custom_exception_handler(client: TestClient):
    response = client.get("/trigger-custom-error")
    assert response.status_code == 418
    assert "custom error" in response.json()["message"].lower()
```

## Test Organization

### Structure

```
tests/
├── conftest.py           # Shared fixtures
├── test_main.py          # Basic app tests
├── test_heroes.py        # Hero CRUD tests
├── test_teams.py         # Team CRUD tests
├── test_auth.py          # Authentication tests
├── test_users.py         # User management tests
└── test_integration.py   # Integration tests
```

### Parametrized Tests

```python
import pytest

@pytest.mark.parametrize("item_id,expected_status", [
    (1, 200),
    (999, 404),
    (-1, 422),
])
def test_read_item_various_ids(client: TestClient, item_id: int, expected_status: int):
    response = client.get(f"/items/{item_id}")
    assert response.status_code == expected_status
```

## Coverage

```bash
# Install coverage
pip install pytest-cov

# Run tests with coverage
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Best Practices

1. **Use fixtures**: Share setup code across tests
2. **Test database isolation**: Use in-memory SQLite or transactions
3. **Mock external services**: Don't call real APIs in tests
4. **Test edge cases**: Invalid input, missing data, errors
5. **Test authentication**: Both success and failure cases
6. **Use parametrized tests**: Test multiple scenarios efficiently
7. **Keep tests fast**: Use in-memory databases, mock slow operations
8. **Test one thing**: Each test should verify one behavior
9. **Clear test names**: `test_create_hero_with_invalid_age`
10. **Clean up**: Reset state between tests

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_heroes.py

# Run specific test
pytest tests/test_heroes.py::test_create_hero

# Run with verbose output
pytest -v

# Run with print statements
pytest -s

# Run only failed tests
pytest --lf

# Run in parallel (faster)
pip install pytest-xdist
pytest -n auto
```
