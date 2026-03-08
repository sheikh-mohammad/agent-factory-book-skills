# Deployment Guide

Production deployment patterns for FastAPI applications.

## Docker Deployment

### Basic Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /code

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy application
COPY ./app /code/app

# Run with uvicorn
CMD ["fastapi", "run", "app/main.py", "--port", "80"]
```

### Multi-Stage Dockerfile (Optimized)

```dockerfile
# Build stage
FROM python:3.12-slim as builder

WORKDIR /code

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Runtime stage
FROM python:3.12-slim

WORKDIR /code

# Copy dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application
COPY ./app /code/app

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /code
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost/health')"

# Run application
CMD ["fastapi", "run", "app/main.py", "--port", "80"]
```

### Multi-Worker Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./app /code/app

# Run with multiple workers
CMD ["fastapi", "run", "app/main.py", "--port", "80", "--workers", "4"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:80"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
    env_file:
      - .env
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=appdb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

### Build and Run

```bash
# Build image
docker build -t fastapi-app .

# Run container
docker run -d -p 8000:80 --env-file .env fastapi-app

# With docker-compose
docker-compose up -d
```

## Uvicorn Production Settings

### Direct Uvicorn

```bash
# Single worker
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Multiple workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# With proxy headers (behind nginx/traefik)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers

# With SSL
uvicorn app.main:app --host 0.0.0.0 --port 443 \
    --ssl-keyfile=/path/to/key.pem \
    --ssl-certfile=/path/to/cert.pem
```

### Gunicorn + Uvicorn Workers

```bash
pip install gunicorn

# Run with gunicorn
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile -
```

## Environment Configuration

### Settings Management

```python
# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    app_name: str = "FastAPI App"
    debug: bool = False

    # Database
    database_url: str

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Logging
    log_level: str = "INFO"

    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }

@lru_cache
def get_settings():
    return Settings()

settings = get_settings()
```

### Environment Files

```bash
# .env.example
APP_NAME=FastAPI App
DEBUG=false

DATABASE_URL=postgresql://user:password@host/db?sslmode=require

SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

CORS_ORIGINS=["https://yourdomain.com"]

LOG_LEVEL=INFO
```

## Cloud Deployment

### AWS (Elastic Beanstalk)

```yaml
# .ebextensions/python.config
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: app.main:app
  aws:elasticbeanstalk:application:environment:
    DATABASE_URL: your-database-url
    SECRET_KEY: your-secret-key
```

```bash
# Deploy
eb init -p python-3.12 fastapi-app
eb create fastapi-env
eb deploy
```

### AWS (ECS with Fargate)

```json
// task-definition.json
{
  "family": "fastapi-app",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "fastapi",
      "image": "your-ecr-repo/fastapi-app:latest",
      "portMappings": [
        {
          "containerPort": 80,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "your-database-url"
        }
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:name"
        }
      ]
    }
  ]
}
```

### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/fastapi-app

# Deploy
gcloud run deploy fastapi-app \
    --image gcr.io/PROJECT_ID/fastapi-app \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars DATABASE_URL=your-url \
    --set-secrets SECRET_KEY=secret-key:latest
```

### Azure App Service

```bash
# Login
az login

# Create resource group
az group create --name fastapi-rg --location eastus

# Create app service plan
az appservice plan create --name fastapi-plan --resource-group fastapi-rg --sku B1 --is-linux

# Create web app
az webapp create --resource-group fastapi-rg --plan fastapi-plan --name fastapi-app --runtime "PYTHON:3.12"

# Deploy
az webapp up --name fastapi-app --resource-group fastapi-rg
```

## Traditional Server (VPS)

### Systemd Service

```ini
# /etc/systemd/system/fastapi.service
[Unit]
Description=FastAPI Application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/fastapi-app
Environment="PATH=/var/www/fastapi-app/venv/bin"
ExecStart=/var/www/fastapi-app/venv/bin/gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable fastapi
sudo systemctl start fastapi
sudo systemctl status fastapi
```

### Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/fastapi
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/fastapi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

## Health Checks

```python
# app/main.py
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/health/db")
async def health_check_db(session: SessionDep):
    try:
        await session.execute(select(1))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database unavailable")
```

## Logging

```python
# app/main.py
import logging
from app.config import settings

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Status: {response.status_code}")
    return response
```

## Monitoring

### Prometheus Metrics

```bash
pip install prometheus-fastapi-instrumentator
```

```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

Instrumentator().instrument(app).expose(app)
```

## Production Checklist

### Security
- [ ] HTTPS enabled
- [ ] Secrets in environment variables (not code)
- [ ] CORS configured restrictively
- [ ] Rate limiting implemented
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (use ORM)
- [ ] Authentication on sensitive endpoints

### Performance
- [ ] Multiple workers configured
- [ ] Database connection pooling
- [ ] Caching implemented (Redis)
- [ ] Static files served by CDN
- [ ] Gzip compression enabled
- [ ] Database indexes on queried fields

### Reliability
- [ ] Health check endpoints
- [ ] Graceful shutdown handling
- [ ] Database migrations automated
- [ ] Backup strategy in place
- [ ] Error tracking (Sentry)
- [ ] Logging configured
- [ ] Monitoring set up

### Operations
- [ ] CI/CD pipeline configured
- [ ] Automated tests passing
- [ ] Documentation updated
- [ ] Environment variables documented
- [ ] Rollback plan defined
- [ ] Scaling strategy defined
