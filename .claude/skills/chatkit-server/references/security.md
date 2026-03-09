# Security Best Practices

Comprehensive security guide for ChatKit applications.

---

## Security Principles

1. **Defense in Depth**: Multiple layers of security
2. **Least Privilege**: Minimal permissions required
3. **Fail Secure**: Errors should not expose data
4. **Input Validation**: Never trust user input
5. **Output Encoding**: Prevent injection attacks

---

## API Key Security

### Environment Variables

```python
# ✅ CORRECT: Use environment variables
import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ❌ WRONG: Hardcoded keys
OPENAI_API_KEY = "sk-proj-abc123..."
```

### Secrets Management

```python
# Production: Use secrets manager
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

def get_api_key():
    """Retrieve API key from Azure Key Vault."""
    credential = DefaultAzureCredential()
    client = SecretClient(
        vault_url="https://your-vault.vault.azure.net/",
        credential=credential
    )
    return client.get_secret("openai-api-key").value
```

### Key Rotation

```python
# Support multiple keys for zero-downtime rotation
OPENAI_API_KEYS = [
    os.getenv("OPENAI_API_KEY_PRIMARY"),
    os.getenv("OPENAI_API_KEY_SECONDARY")
]

def get_client():
    """Get OpenAI client with fallback keys."""
    for key in OPENAI_API_KEYS:
        if key:
            try:
                client = OpenAI(api_key=key)
                # Test key validity
                client.models.list()
                return client
            except Exception:
                continue
    raise Exception("No valid API keys available")
```

---

## Input Validation

### Sanitize User Input

```python
import html
import re
from typing import Optional

def sanitize_text(text: str, max_length: int = 10000) -> str:
    """Sanitize user input."""
    # Remove null bytes
    text = text.replace('\x00', '')

    # Limit length
    text = text[:max_length]

    # Escape HTML
    text = html.escape(text)

    # Remove control characters except newlines/tabs
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)

    return text.strip()

@app.post("/chat")
async def chat(request: ChatRequest):
    # Sanitize input
    clean_message = sanitize_text(request.message)

    if not clean_message:
        raise HTTPException(status_code=400, detail="Empty message")

    # Process clean message
    response = await process_chat(clean_message)
    return response
```

### Validate Tool Parameters

```python
from pydantic import BaseModel, validator, Field

class EmailToolParams(BaseModel):
    to: str = Field(..., max_length=254)
    subject: str = Field(..., max_length=200)
    body: str = Field(..., max_length=10000)

    @validator('to')
    def validate_email(cls, v):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email address')
        return v

    @validator('subject', 'body')
    def validate_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Field cannot be empty')
        return v

def send_email_tool(params: EmailToolParams) -> dict:
    """Send email with validated parameters."""
    # Parameters are already validated by Pydantic
    return send_email(params.to, params.subject, params.body)
```

---

## Authentication & Authorization

### API Key Authentication

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key."""
    valid_keys = os.getenv("VALID_API_KEYS", "").split(",")
    if api_key not in valid_keys:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@app.post("/chat")
async def chat(
    request: ChatRequest,
    api_key: str = Security(verify_api_key)
):
    # API key verified
    return await process_chat(request)
```

### JWT Authentication

```python
from fastapi import Depends
from fastapi.security import HTTPBearer
from jose import JWTError, jwt

security = HTTPBearer()
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"

def verify_token(credentials = Depends(security)):
    """Verify JWT token."""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/chat")
async def chat(
    request: ChatRequest,
    user_id: str = Depends(verify_token)
):
    # User authenticated
    return await process_chat(request, user_id)
```

### Role-Based Access Control

```python
from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

def check_permission(user_id: str, required_role: Role) -> bool:
    """Check if user has required role."""
    user = get_user(user_id)
    role_hierarchy = {
        Role.ADMIN: 3,
        Role.USER: 2,
        Role.GUEST: 1
    }
    return role_hierarchy.get(user.role, 0) >= role_hierarchy.get(required_role, 0)

def require_role(required_role: Role):
    """Decorator to require specific role."""
    def decorator(func):
        async def wrapper(*args, user_id: str = None, **kwargs):
            if not check_permission(user_id, required_role):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return await func(*args, user_id=user_id, **kwargs)
        return wrapper
    return decorator

@app.post("/admin/chat")
@require_role(Role.ADMIN)
async def admin_chat(request: ChatRequest, user_id: str = Depends(verify_token)):
    return await process_admin_chat(request)
```

---

## Rate Limiting

### Per-User Rate Limiting

```python
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import HTTPException

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    def check_rate_limit(self, user_id: str) -> bool:
        """Check if user is within rate limit."""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)

        # Remove old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if req_time > window_start
        ]

        # Check limit
        if len(self.requests[user_id]) >= self.max_requests:
            return False

        # Record request
        self.requests[user_id].append(now)
        return True

# 10 requests per minute
rate_limiter = RateLimiter(max_requests=10, window_seconds=60)

@app.post("/chat")
async def chat(request: ChatRequest, user_id: str = Depends(verify_token)):
    if not rate_limiter.check_rate_limit(user_id):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again later."
        )
    return await process_chat(request)
```

### Token Bucket Algorithm

```python
import time

class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens."""
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def _refill(self):
        """Refill tokens based on time elapsed."""
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

# Per-user buckets
user_buckets = defaultdict(lambda: TokenBucket(capacity=100, refill_rate=1.0))

@app.post("/chat")
async def chat(request: ChatRequest, user_id: str = Depends(verify_token)):
    if not user_buckets[user_id].consume():
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return await process_chat(request)
```

---

## Data Protection

### PII Redaction

```python
import re

def redact_pii(text: str) -> str:
    """Redact personally identifiable information."""
    # Email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)

    # Phone numbers (US format)
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)

    # SSN
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)

    # Credit card numbers
    text = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]', text)

    return text

@app.post("/chat")
async def chat(request: ChatRequest):
    # Redact PII before logging
    safe_message = redact_pii(request.message)
    logger.info(f"Chat request: {safe_message}")

    # Process original message
    response = await process_chat(request.message)
    return response
```

### Encryption at Rest

```python
from cryptography.fernet import Fernet

class DataEncryption:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)

    def encrypt(self, data: str) -> str:
        """Encrypt data."""
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data."""
        return self.cipher.decrypt(encrypted_data.encode()).decode()

# Initialize with key from environment
encryption_key = os.getenv("ENCRYPTION_KEY").encode()
encryptor = DataEncryption(encryption_key)

def store_sensitive_data(user_id: str, data: str):
    """Store encrypted sensitive data."""
    encrypted = encryptor.encrypt(data)
    db.execute(
        "INSERT INTO sensitive_data (user_id, data) VALUES (?, ?)",
        (user_id, encrypted)
    )
```

---

## SQL Injection Prevention

### Use Parameterized Queries

```python
# ✅ CORRECT: Parameterized query
def get_user(user_id: str):
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()

# ❌ WRONG: String concatenation
def get_user_unsafe(user_id: str):
    cursor.execute(f"SELECT * FROM users WHERE id = '{user_id}'")
    return cursor.fetchone()
```

### Use ORM

```python
from sqlalchemy import select

# SQLAlchemy automatically parameterizes
def get_user(user_id: str):
    stmt = select(User).where(User.id == user_id)
    return session.execute(stmt).scalar_one_or_none()
```

---

## CORS Configuration

### Restrictive CORS

```python
from fastapi.middleware.cors import CORSMiddleware

# ✅ CORRECT: Specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://app.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=3600
)

# ❌ WRONG: Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Security risk!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

---

## Logging Security

### Safe Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.post("/chat")
async def chat(request: ChatRequest, user_id: str = Depends(verify_token)):
    # ✅ CORRECT: Log without sensitive data
    logger.info(f"Chat request from user {user_id[:8]}...")

    # ❌ WRONG: Log sensitive data
    # logger.info(f"Message: {request.message}")
    # logger.info(f"API Key: {OPENAI_API_KEY}")

    response = await process_chat(request)
    return response
```

---

## Security Headers

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

# Force HTTPS in production
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# Restrict allowed hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

---

## Security Checklist

### Development
- [ ] API keys in environment variables (not code)
- [ ] .env file in .gitignore
- [ ] Input validation on all endpoints
- [ ] Output encoding/sanitization
- [ ] CORS configured for localhost only

### Production
- [ ] Secrets in secrets manager (AWS/Azure/GCP)
- [ ] HTTPS enabled with valid certificate
- [ ] Authentication implemented
- [ ] Authorization/RBAC configured
- [ ] Rate limiting enabled
- [ ] PII redaction in logs
- [ ] Encryption at rest for sensitive data
- [ ] SQL injection prevention (parameterized queries)
- [ ] CORS restricted to production domains
- [ ] Security headers configured
- [ ] Regular security audits scheduled
- [ ] Dependency vulnerability scanning
- [ ] Incident response plan documented

### Compliance
- [ ] GDPR compliance (if EU users)
- [ ] HIPAA compliance (if healthcare data)
- [ ] PCI DSS compliance (if payment data)
- [ ] SOC 2 compliance (if enterprise)
- [ ] Data retention policies implemented
- [ ] Privacy policy published
- [ ] Terms of service published
