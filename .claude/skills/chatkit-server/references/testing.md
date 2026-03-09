# Testing Strategies

Comprehensive testing guide for ChatKit applications.

---

## Testing Pyramid

```
        /\
       /  \      E2E Tests (10%)
      /----\     Integration Tests (30%)
     /------\    Unit Tests (60%)
    /--------\
```

---

## Unit Testing

### Testing Tools

```python
# requirements-dev.txt
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
httpx==0.25.2  # For testing FastAPI
```

### Testing Custom Tools

```python
# tests/test_tools.py
import pytest
from app.tools.user_tools import get_user_info, update_user_profile

def test_get_user_info_success():
    """Test successful user retrieval."""
    result = get_user_info("user_123")

    assert result["success"] is True
    assert result["user_id"] == "user_123"
    assert "name" in result
    assert "email" in result

def test_get_user_info_not_found():
    """Test user not found."""
    result = get_user_info("nonexistent")

    assert result["success"] is False
    assert "error" in result
    assert result["error_code"] == "USER_NOT_FOUND"

def test_get_user_info_invalid_input():
    """Test invalid input handling."""
    result = get_user_info("")

    assert result["success"] is False
    assert result["error_code"] == "INVALID_INPUT"

@pytest.mark.parametrize("user_id,expected", [
    ("user_123", True),
    ("user_456", True),
    ("", False),
    (None, False),
])
def test_get_user_info_parametrized(user_id, expected):
    """Test multiple scenarios."""
    result = get_user_info(user_id)
    assert result["success"] == expected
```

### Testing with Mocks

```python
from unittest.mock import Mock, patch
import pytest

@patch('app.tools.user_tools.db')
def test_get_user_with_mock(mock_db):
    """Test with mocked database."""
    # Setup mock
    mock_user = Mock()
    mock_user.id = "user_123"
    mock_user.name = "John Doe"
    mock_user.email = "john@example.com"

    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    # Test
    result = get_user_info("user_123")

    # Verify
    assert result["success"] is True
    assert result["name"] == "John Doe"
    mock_db.query.assert_called_once()
```

### Testing Async Functions

```python
import pytest
from app.main import process_chat

@pytest.mark.asyncio
async def test_process_chat():
    """Test async chat processing."""
    request = ChatRequest(message="Hello", thread_id=None)
    response = await process_chat(request)

    assert "response" in response
    assert "thread_id" in response
    assert response["thread_id"] is not None
```

---

## Integration Testing

### Testing FastAPI Endpoints

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app
import os

# Set test environment variables
os.environ["OPENAI_API_KEY"] = "test-key"

client = TestClient(app)

def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_chat_endpoint_success():
    """Test successful chat request."""
    response = client.post(
        "/chat",
        json={"message": "Hello", "thread_id": None}
    )

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "thread_id" in data

def test_chat_endpoint_validation_error():
    """Test validation error handling."""
    response = client.post(
        "/chat",
        json={"message": ""}  # Empty message
    )

    assert response.status_code == 422

def test_chat_endpoint_authentication():
    """Test authentication requirement."""
    response = client.post(
        "/chat",
        json={"message": "Hello"},
        headers={"X-API-Key": "invalid-key"}
    )

    assert response.status_code == 403
```

### Testing with OpenAI Mock

```python
from unittest.mock import Mock, patch

@patch('app.main.client')
def test_chat_with_openai_mock(mock_client):
    """Test chat with mocked OpenAI client."""
    # Setup mock response
    mock_thread = Mock()
    mock_thread.id = "thread_123"
    mock_client.beta.threads.create.return_value = mock_thread

    mock_message = Mock()
    mock_message.content = [Mock(text=Mock(value="Hello! How can I help?"))]
    mock_messages = Mock()
    mock_messages.data = [mock_message]
    mock_client.beta.threads.messages.list.return_value = mock_messages

    # Test
    response = client.post(
        "/chat",
        json={"message": "Hello", "thread_id": None}
    )

    assert response.status_code == 200
    assert "Hello! How can I help?" in response.json()["response"]
```

### Testing Tool Execution

```python
def test_tool_execution_flow():
    """Test complete tool execution flow."""
    # Mock tool call
    with patch('app.main.TOOL_FUNCTIONS') as mock_tools:
        mock_tools["get_weather"].return_value = {
            "temperature": 72,
            "condition": "sunny"
        }

        response = client.post(
            "/chat",
            json={"message": "What's the weather?"}
        )

        assert response.status_code == 200
        # Verify tool was called
        mock_tools["get_weather"].assert_called()
```

---

## End-to-End Testing

### Full Conversation Flow

```python
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def chat_session():
    """Create a chat session for testing."""
    return {"thread_id": None}

def test_full_conversation_flow(chat_session):
    """Test complete conversation with thread continuity."""
    # First message
    response1 = client.post(
        "/chat",
        json={"message": "My name is Alice", "thread_id": chat_session["thread_id"]}
    )
    assert response1.status_code == 200
    chat_session["thread_id"] = response1.json()["thread_id"]

    # Second message (should remember context)
    response2 = client.post(
        "/chat",
        json={"message": "What's my name?", "thread_id": chat_session["thread_id"]}
    )
    assert response2.status_code == 200
    assert "Alice" in response2.json()["response"]
```

### Testing Vector Store Integration

```python
@pytest.mark.integration
def test_knowledge_retrieval():
    """Test knowledge retrieval from vector store."""
    response = client.post(
        "/chat",
        json={
            "message": "What is our refund policy?",
            "thread_id": None
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "citations" in data
    assert len(data["citations"]) > 0
```

### Testing Multi-Agent Handoff

```python
def test_agent_handoff():
    """Test handoff between agents."""
    # Start with router agent
    response1 = client.post(
        "/chat",
        json={
            "message": "I need help with billing",
            "thread_id": None
        }
    )

    assert response1.status_code == 200
    data = response1.json()

    # Should handoff to billing agent
    if "handoff" in data:
        assert data["next_agent"] == "billing"

        # Continue with billing agent
        response2 = client.post(
            "/chat",
            json={
                "message": "Show my invoice",
                "thread_id": data["thread_id"],
                "current_agent": "billing"
            }
        )
        assert response2.status_code == 200
```

---

## Load Testing

### Using Locust

```python
# locustfile.py
from locust import HttpUser, task, between

class ChatKitUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Initialize user session."""
        self.thread_id = None

    @task(3)
    def send_message(self):
        """Send chat message."""
        response = self.client.post(
            "/chat",
            json={
                "message": "Hello, how are you?",
                "thread_id": self.thread_id
            }
        )

        if response.status_code == 200:
            data = response.json()
            self.thread_id = data.get("thread_id")

    @task(1)
    def health_check(self):
        """Check health endpoint."""
        self.client.get("/health")

# Run: locust -f locustfile.py --host=http://localhost:8000
```

### Performance Benchmarks

```python
import time
import statistics

def benchmark_chat_endpoint(num_requests=100):
    """Benchmark chat endpoint performance."""
    response_times = []

    for _ in range(num_requests):
        start = time.time()
        response = client.post(
            "/chat",
            json={"message": "Test message"}
        )
        duration = time.time() - start

        if response.status_code == 200:
            response_times.append(duration)

    return {
        "mean": statistics.mean(response_times),
        "median": statistics.median(response_times),
        "p95": statistics.quantiles(response_times, n=20)[18],
        "p99": statistics.quantiles(response_times, n=100)[98]
    }

def test_performance_benchmarks():
    """Test performance meets requirements."""
    results = benchmark_chat_endpoint(100)

    # Assert performance requirements
    assert results["mean"] < 2.0, "Mean response time should be under 2s"
    assert results["p95"] < 5.0, "P95 should be under 5s"
    assert results["p99"] < 10.0, "P99 should be under 10s"
```

---

## Test Fixtures

### Reusable Test Data

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def test_client():
    """Create test client."""
    return TestClient(app)

@pytest.fixture
def sample_user():
    """Sample user data."""
    return {
        "id": "user_123",
        "name": "Test User",
        "email": "test@example.com"
    }

@pytest.fixture
def sample_chat_request():
    """Sample chat request."""
    return {
        "message": "Hello, world!",
        "thread_id": None
    }

@pytest.fixture
def mock_openai_client(mocker):
    """Mock OpenAI client."""
    mock = mocker.patch('app.main.client')

    # Setup default responses
    mock_thread = mocker.Mock()
    mock_thread.id = "thread_123"
    mock.beta.threads.create.return_value = mock_thread

    return mock
```

---

## Coverage Testing

### Measuring Code Coverage

```bash
# Run tests with coverage
pytest --cov=app --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html
```

### Coverage Configuration

```ini
# .coveragerc
[run]
source = app
omit =
    */tests/*
    */venv/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```

### Coverage Requirements

```python
# tests/test_coverage.py
import pytest
import subprocess

def test_minimum_coverage():
    """Ensure minimum code coverage."""
    result = subprocess.run(
        ["pytest", "--cov=app", "--cov-report=term-missing"],
        capture_output=True,
        text=True
    )

    # Parse coverage percentage
    for line in result.stdout.split('\n'):
        if 'TOTAL' in line:
            coverage = float(line.split()[-1].rstrip('%'))
            assert coverage >= 80, f"Coverage {coverage}% is below 80%"
```

---

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run tests
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      run: |
        pytest --cov=app --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

---

## Testing Best Practices

### 1. Test Isolation

```python
@pytest.fixture(autouse=True)
def reset_database():
    """Reset database before each test."""
    db.drop_all()
    db.create_all()
    yield
    db.session.remove()
```

### 2. Test Naming Convention

```python
# Good: Descriptive test names
def test_chat_endpoint_returns_response_with_valid_input():
    pass

def test_chat_endpoint_raises_validation_error_with_empty_message():
    pass

# Bad: Vague test names
def test_chat():
    pass

def test_error():
    pass
```

### 3. Arrange-Act-Assert Pattern

```python
def test_user_creation():
    # Arrange
    user_data = {"name": "John", "email": "john@example.com"}

    # Act
    result = create_user(user_data)

    # Assert
    assert result["success"] is True
    assert result["user"]["name"] == "John"
```

### 4. Test One Thing

```python
# Good: Test one behavior
def test_user_creation_success():
    result = create_user(valid_data)
    assert result["success"] is True

def test_user_creation_duplicate_email():
    create_user({"email": "test@example.com"})
    result = create_user({"email": "test@example.com"})
    assert result["error_code"] == "DUPLICATE_EMAIL"

# Bad: Test multiple behaviors
def test_user_creation():
    # Tests success, duplicate, validation, etc.
    pass
```

---

## Testing Checklist

### Unit Tests
- [ ] All custom tools tested
- [ ] Input validation tested
- [ ] Error handling tested
- [ ] Edge cases covered
- [ ] Mocks used for external dependencies

### Integration Tests
- [ ] API endpoints tested
- [ ] Authentication tested
- [ ] Tool execution flow tested
- [ ] Database operations tested
- [ ] OpenAI integration tested (with mocks)

### E2E Tests
- [ ] Full conversation flows tested
- [ ] Thread continuity tested
- [ ] Vector store integration tested
- [ ] Multi-agent handoffs tested (if applicable)

### Performance Tests
- [ ] Load testing completed
- [ ] Response time benchmarks met
- [ ] Concurrent user testing done
- [ ] Memory usage profiled

### Coverage
- [ ] Minimum 80% code coverage
- [ ] Critical paths 100% covered
- [ ] Coverage report generated

### CI/CD
- [ ] Tests run on every commit
- [ ] Coverage tracked over time
- [ ] Failed tests block deployment
