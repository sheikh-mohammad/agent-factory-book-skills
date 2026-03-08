# Setup and Configuration

Complete guide for installing and configuring Google ADK.

## Installation

### Using pip
```bash
pip install google-adk
```

### Using uv (recommended for faster installs)
```bash
uv pip install google-adk

# With all extras
uv sync --all-extras
```

### Virtual Environment Setup
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

# Install ADK
pip install google-adk
```

## Authentication Configuration

### Option 1: Google AI Studio (Development)

Best for: Development, prototyping, personal projects

**Get API Key:**
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create or select a project
3. Generate API key

**Configure:**
```bash
export GOOGLE_API_KEY=your_api_key_here
```

**In .env file:**
```bash
GOOGLE_GENAI_USE_VERTEXAI=0
GOOGLE_API_KEY=your_api_key_here
```

### Option 2: Vertex AI (Production)

Best for: Production deployments, enterprise applications, GCP integration

**Prerequisites:**
1. Google Cloud Project with billing enabled
2. Vertex AI API enabled
3. Application Default Credentials configured

**Configure:**
```bash
# Set up authentication
gcloud auth application-default login

# Set environment variables
export GOOGLE_GENAI_USE_VERTEXAI=1
export GOOGLE_CLOUD_PROJECT=your_project_id
export GOOGLE_CLOUD_LOCATION=us-central1
```

**In .env file:**
```bash
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1
```

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GOOGLE_API_KEY` | For AI Studio | API key from Google AI Studio | `AIza...` |
| `GOOGLE_GENAI_USE_VERTEXAI` | Yes | Backend selection (0=AI Studio, 1=Vertex AI) | `1` |
| `GOOGLE_CLOUD_PROJECT` | For Vertex AI | GCP project ID | `my-project-123` |
| `GOOGLE_CLOUD_LOCATION` | For Vertex AI | GCP region | `us-central1` |
| `POSTGRES_URL` | Optional | PostgreSQL connection for sessions | `postgresql+asyncpg://...` |
| `OLLAMA_API_BASE` | Optional | Ollama API endpoint for local models | `http://localhost:11434` |

## Project Structure

### Minimal Structure
```
my-agent-project/
├── .env                 # Environment variables
├── agent.py            # Agent definition
└── requirements.txt    # Dependencies
```

### Production Structure
```
my-agent-project/
├── .env                # Environment variables (gitignored)
├── agents/             # Agent definitions
│   ├── __init__.py
│   ├── main_agent.py
│   └── sub_agents/
├── tools/              # Custom tools
│   ├── __init__.py
│   └── custom_tools.py
├── config/             # Configuration
│   ├── __init__.py
│   └── settings.py
├── tests/              # Tests
│   └── test_agent.py
├── requirements.txt    # Dependencies
└── README.md          # Documentation
```

## Configuration Best Practices

### Development
- Use Google AI Studio for faster iteration
- Store credentials in `.env` file (add to `.gitignore`)
- Use `InMemoryRunner` for quick testing
- Enable verbose logging for debugging

### Production
- Use Vertex AI for managed infrastructure
- Store secrets in Google Secret Manager
- Use managed services (VertexAiSessionService, VertexAiRagMemoryService)
- Implement proper error handling and monitoring
- Use environment-specific configuration files

## Model Selection

### Available Models

| Model | Best For | Context Window | Speed |
|-------|----------|----------------|-------|
| `gemini-2.5-flash` | Fast responses, high throughput | 1M tokens | Very Fast |
| `gemini-2.5-pro` | Complex reasoning, analysis | 2M tokens | Moderate |
| `gemini-1.5-flash` | Legacy support | 1M tokens | Fast |
| `gemini-1.5-pro` | Legacy support | 2M tokens | Moderate |

### Model Configuration

```python
from google.adk import Agent
from google.genai import types

agent = Agent(
    name="assistant",
    model="gemini-2.5-flash",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.7,
        top_p=0.95,
        top_k=40,
        max_output_tokens=8192,
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            ),
        ],
    ),
)
```

## Verification

### Test Installation
```python
from google.adk import Agent
from google.adk.runners import InMemoryRunner
import asyncio

agent = Agent(
    name="test",
    model="gemini-2.5-flash",
    instruction="You are a test assistant.",
)

runner = InMemoryRunner(agent=agent, app_name="test")

async def test():
    await runner.run_debug("Hello!")

asyncio.run(test())
```

### Test Authentication

**AI Studio:**
```bash
# Should return model info without errors
python -c "from google.genai import Client; client = Client(api_key='$GOOGLE_API_KEY'); print('Auth OK')"
```

**Vertex AI:**
```bash
# Should list models without errors
gcloud ai models list --region=us-central1
```

## Troubleshooting

### Common Issues

**Issue: `GOOGLE_API_KEY not found`**
- Solution: Ensure `.env` file is in project root and loaded
- Use `python-dotenv` to load: `from dotenv import load_dotenv; load_dotenv()`

**Issue: `Permission denied` with Vertex AI**
- Solution: Run `gcloud auth application-default login`
- Ensure service account has Vertex AI User role

**Issue: `Model not found`**
- Solution: Check model name spelling (e.g., `gemini-2.5-flash` not `gemini-2-5-flash`)
- Verify model is available in your region

**Issue: Rate limiting errors**
- Solution: Implement exponential backoff
- Consider upgrading quota in Google Cloud Console
- Use `gemini-2.5-flash` for higher throughput

## Next Steps

After setup:
1. Create your first agent (see core-concepts.md)
2. Add tools for specific capabilities (see tools-integration.md)
3. Test locally with `adk web`
4. Deploy to production (see deployment.md)
