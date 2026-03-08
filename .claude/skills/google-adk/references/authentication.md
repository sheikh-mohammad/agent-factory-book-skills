# Authentication and Security

Comprehensive guide for securing tool access and API communications in Google ADK.

## Overview

ADK provides authentication frameworks for securing:
- Tool access to external APIs
- User-specific data access
- Multi-tenant agent systems
- OAuth flows and token management

## Authentication Methods

| Method | Use Case | Complexity |
|--------|----------|------------|
| **API Key** | Simple API access, development | Low |
| **OAuth2 Client Credentials** | Service-to-service authentication | Medium |
| **OAuth2 Authorization Code** | User-delegated access | High |
| **Service Account** | GCP service authentication | Medium |
| **Custom Handlers** | Proprietary auth schemes | Variable |

## API Key Authentication

Simplest method for APIs that use API keys.

### Basic API Key

```python
from google.adk.tools import AuthenticatedFunctionTool
from google.adk.tools.authentication import ApiKeyCredentialExchanger

def call_api(endpoint: str) -> dict:
    """Call external API."""
    # Function receives authenticated HTTP client
    pass

auth_tool = AuthenticatedFunctionTool(
    function=call_api,
    credential_exchanger=ApiKeyCredentialExchanger(
        api_key="your_api_key",
        header_name="X-API-Key",  # Default: "Authorization"
    ),
)

agent = Agent(
    name="api_assistant",
    model="gemini-2.5-flash",
    tools=[auth_tool],
)
```

### API Key from Environment

```python
import os

auth_tool = AuthenticatedFunctionTool(
    function=call_api,
    credential_exchanger=ApiKeyCredentialExchanger(
        api_key=os.getenv("API_KEY"),
        header_name="X-API-Key",
    ),
)
```

### Bearer Token

```python
auth_tool = AuthenticatedFunctionTool(
    function=call_api,
    credential_exchanger=ApiKeyCredentialExchanger(
        api_key="your_token",
        header_name="Authorization",
        prefix="Bearer",  # Results in "Authorization: Bearer your_token"
    ),
)
```

## OAuth2 Client Credentials

For service-to-service authentication.

### Basic OAuth2 Setup

```python
from google.adk.tools.authentication import OAuth2CredentialExchanger

def get_weather_data(city: str) -> dict:
    """Get weather data from authenticated API."""
    pass

auth_tool = AuthenticatedFunctionTool(
    function=get_weather_data,
    credential_exchanger=OAuth2CredentialExchanger(
        client_id="your_client_id",
        client_secret="your_client_secret",
        token_url="https://oauth.example.com/token",
        scopes=["read:weather", "read:forecast"],
    ),
)
```

### OAuth2 with Credential Manager

For managing multiple credentials:

```python
from google.adk.tools.authentication import CredentialManager

credential_manager = CredentialManager()

# Register credentials
credential_manager.register(
    name="weather_api",
    exchanger=OAuth2CredentialExchanger(
        client_id=os.getenv("WEATHER_CLIENT_ID"),
        client_secret=os.getenv("WEATHER_CLIENT_SECRET"),
        token_url="https://oauth.weather.com/token",
    ),
)

# Use in tool
auth_tool = AuthenticatedFunctionTool(
    function=get_weather_data,
    credential_manager=credential_manager,
    credential_name="weather_api",
)
```

### Token Caching

OAuth2 tokens are automatically cached and refreshed:

```python
# Token is obtained on first call
result1 = await auth_tool.execute({"city": "London"})

# Cached token is reused
result2 = await auth_tool.execute({"city": "Paris"})

# Token is automatically refreshed when expired
result3 = await auth_tool.execute({"city": "Tokyo"})
```

## OAuth2 Authorization Code Flow

For user-delegated access (A2A pattern).

### A2A OAuth Authentication

```python
from google.adk.agents import LlmAgent

# Remote agent that needs OAuth
remote_agent = LlmAgent(
    name="bigquery_agent",
    model="gemini-2.5-flash",
    instruction="""You help users query BigQuery.
    When you need OAuth credentials, surface the authentication request
    to the root agent.""",
    tools=[bigquery_tools],
)

# Root agent handles OAuth flow
root_agent = LlmAgent(
    name="root_agent",
    model="gemini-2.5-flash",
    instruction="""You coordinate with sub-agents.
    When a sub-agent needs OAuth, guide the user through the flow.""",
    sub_agents=[remote_agent],
)
```

### OAuth Flow Steps

1. Remote agent surfaces OAuth request to root agent
2. Root agent guides user through OAuth flow
3. User authorizes access
4. Credentials returned to remote agent
5. Remote agent accesses protected resources

See official documentation for complete A2A OAuth examples:
- [A2A OAuth Authentication Sample](https://github.com/google/adk-python/blob/main/contributing/samples/a2a_auth/README.md)

## OpenAPI with Authentication

Authenticate OpenAPI tools.

### OpenAPI with API Key

```python
from google.adk.tools import OpenApiToolset

api_tools = OpenApiToolset(
    spec_url="https://api.example.com/openapi.json",
    auth_config={
        "type": "apiKey",
        "name": "X-API-Key",
        "in": "header",
        "value": os.getenv("API_KEY"),
    },
)
```

### OpenAPI with OAuth2

```python
api_tools = OpenApiToolset(
    spec_url="https://api.example.com/openapi.json",
    auth_config={
        "type": "oauth2",
        "client_id": os.getenv("CLIENT_ID"),
        "client_secret": os.getenv("CLIENT_SECRET"),
        "token_url": "https://oauth.example.com/token",
        "scopes": ["read", "write"],
    },
)
```

### OpenAPI with Bearer Token

```python
api_tools = OpenApiToolset(
    spec_url="https://api.example.com/openapi.json",
    auth_config={
        "type": "http",
        "scheme": "bearer",
        "bearer_format": "JWT",
        "value": os.getenv("JWT_TOKEN"),
    },
)
```

## Service Account Authentication (GCP)

For Google Cloud services.

### Application Default Credentials

```python
# Set up ADC
# gcloud auth application-default login

# ADK automatically uses ADC for GCP services
from google.adk.tools import BigQueryToolset

bq_tools = BigQueryToolset(
    project_id="your-project-id",
    # Automatically uses ADC
)
```

### Service Account Key File

```python
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/path/to/service-account-key.json"

bq_tools = BigQueryToolset(
    project_id="your-project-id",
)
```

### Service Account Impersonation

```python
from google.auth import impersonated_credentials
from google.auth import default

# Get source credentials
source_credentials, _ = default()

# Impersonate service account
target_credentials = impersonated_credentials.Credentials(
    source_credentials=source_credentials,
    target_principal="service-account@project.iam.gserviceaccount.com",
    target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
)

# Use with tools
bq_tools = BigQueryToolset(
    project_id="your-project-id",
    credentials=target_credentials,
)
```

## Custom Authentication Handlers

For proprietary or complex auth schemes.

### Custom Credential Exchanger

```python
from google.adk.tools.authentication import BaseCredentialExchanger

class CustomAuthExchanger(BaseCredentialExchanger):
    def __init__(self, api_key: str, secret: str):
        self.api_key = api_key
        self.secret = secret

    async def get_credentials(self) -> dict:
        """Generate custom auth headers."""
        # Custom logic to generate token
        token = self._generate_token(self.api_key, self.secret)

        return {
            "headers": {
                "X-Custom-Auth": token,
                "X-API-Key": self.api_key,
            }
        }

    def _generate_token(self, api_key: str, secret: str) -> str:
        # Custom token generation logic
        import hmac
        import hashlib
        import time

        timestamp = str(int(time.time()))
        message = f"{api_key}:{timestamp}"
        signature = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return f"{api_key}:{timestamp}:{signature}"

# Use custom exchanger
auth_tool = AuthenticatedFunctionTool(
    function=call_api,
    credential_exchanger=CustomAuthExchanger(
        api_key=os.getenv("API_KEY"),
        secret=os.getenv("API_SECRET"),
    ),
)
```

## Security Best Practices

### Credential Storage

**Development:**
```bash
# .env file (add to .gitignore)
API_KEY=your_api_key
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
```

**Production:**
```python
# Use Google Secret Manager
from google.cloud import secretmanager

def get_secret(secret_id: str) -> str:
    """Fetch secret from Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

auth_tool = AuthenticatedFunctionTool(
    function=call_api,
    credential_exchanger=ApiKeyCredentialExchanger(
        api_key=get_secret("api_key"),
    ),
)
```

### Principle of Least Privilege

Grant minimal necessary permissions:

```python
# Good - specific scopes
OAuth2CredentialExchanger(
    client_id="...",
    client_secret="...",
    token_url="...",
    scopes=["read:orders", "write:orders"],  # Only what's needed
)

# Bad - overly broad scopes
OAuth2CredentialExchanger(
    client_id="...",
    client_secret="...",
    token_url="...",
    scopes=["admin"],  # Too much access
)
```

### Token Rotation

Implement token rotation for long-lived agents:

```python
import time

class RotatingTokenExchanger(BaseCredentialExchanger):
    def __init__(self, token_generator):
        self.token_generator = token_generator
        self.token = None
        self.token_expiry = 0

    async def get_credentials(self) -> dict:
        now = time.time()
        if not self.token or now >= self.token_expiry:
            # Refresh token
            self.token = await self.token_generator()
            self.token_expiry = now + 3600  # 1 hour

        return {"headers": {"Authorization": f"Bearer {self.token}"}}
```

### Audit Logging

Log authentication events:

```python
import logging

logger = logging.getLogger(__name__)

async def audit_auth_callback(
    tool: BaseTool,
    args: dict,
    tool_context: ToolContext,
) -> Optional[dict]:
    """Log authenticated tool calls."""
    if isinstance(tool, AuthenticatedFunctionTool):
        logger.info(
            f"Authenticated call to {tool.name} by user {tool_context.user_id}"
        )
    return None

agent = Agent(
    name="secure_assistant",
    model="gemini-2.5-flash",
    before_tool_callback=audit_auth_callback,
)
```

### Rate Limiting

Implement rate limiting for authenticated endpoints:

```python
from collections import defaultdict
import time

class RateLimitedExchanger(BaseCredentialExchanger):
    def __init__(self, base_exchanger, calls_per_minute=60):
        self.base_exchanger = base_exchanger
        self.calls_per_minute = calls_per_minute
        self.call_times = []

    async def get_credentials(self) -> dict:
        now = time.time()

        # Remove calls older than 1 minute
        self.call_times = [t for t in self.call_times if now - t < 60]

        # Check rate limit
        if len(self.call_times) >= self.calls_per_minute:
            wait_time = 60 - (now - self.call_times[0])
            raise Exception(f"Rate limit exceeded. Wait {wait_time:.1f}s")

        self.call_times.append(now)
        return await self.base_exchanger.get_credentials()
```

## Multi-Tenant Authentication

For agents serving multiple users.

### User-Specific Credentials

```python
from google.adk.tools import ToolContext

class UserCredentialExchanger(BaseCredentialExchanger):
    def __init__(self, credential_store):
        self.credential_store = credential_store

    async def get_credentials(self, tool_context: ToolContext) -> dict:
        """Get credentials for specific user."""
        user_id = tool_context.user_id

        # Fetch user-specific credentials
        user_creds = await self.credential_store.get(user_id)

        if not user_creds:
            raise Exception(f"No credentials found for user {user_id}")

        return {
            "headers": {
                "Authorization": f"Bearer {user_creds['token']}"
            }
        }
```

### Credential Isolation

Ensure credentials are isolated per session:

```python
def create_user_agent(user_id: str, user_token: str) -> Agent:
    """Create agent with user-specific credentials."""

    auth_tool = AuthenticatedFunctionTool(
        function=call_api,
        credential_exchanger=ApiKeyCredentialExchanger(
            api_key=user_token,
        ),
    )

    return Agent(
        name=f"agent_{user_id}",
        model="gemini-2.5-flash",
        tools=[auth_tool],
    )

# Create separate agent instances per user
user1_agent = create_user_agent("user1", "token1")
user2_agent = create_user_agent("user2", "token2")
```

## Troubleshooting

### Common Issues

**Issue: "Invalid credentials"**
- Verify API key/client credentials are correct
- Check environment variables are loaded
- Ensure credentials haven't expired

**Issue: "Token expired"**
- OAuth2 tokens are auto-refreshed; check refresh token is valid
- Verify token_url is correct
- Check system clock is synchronized

**Issue: "Insufficient permissions"**
- Verify scopes include required permissions
- Check service account has necessary IAM roles
- Review API documentation for required scopes

**Issue: "Rate limit exceeded"**
- Implement exponential backoff
- Use token caching to reduce auth calls
- Consider upgrading API tier

### Debug Authentication

Enable verbose logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("google.adk.tools.authentication")
logger.setLevel(logging.DEBUG)
```

Test authentication separately:

```python
# Test credential exchanger
exchanger = OAuth2CredentialExchanger(...)
credentials = await exchanger.get_credentials()
print(f"Token: {credentials}")

# Test authenticated call
auth_tool = AuthenticatedFunctionTool(...)
result = await auth_tool.execute({"param": "value"})
print(f"Result: {result}")
```

## Official Documentation

- [ADK Authentication Guide](https://github.com/google/adk-docs/blob/main/docs/tools/authentication.md)
- [OAuth2 Client Credentials Sample](https://github.com/google/adk-python/blob/main/contributing/samples/oauth2_client_credentials/README.md)
- [A2A OAuth Sample](https://github.com/google/adk-python/blob/main/contributing/samples/a2a_auth/README.md)
- [All-in-One Auth Demo](https://github.com/google/adk-python/blob/main/contributing/samples/authn-adk-all-in-one/README.md)
