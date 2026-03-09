# Production Deployment Guide

Comprehensive guide for deploying ChatKit applications to production.

---

## Deployment Options

| Option | Best For | Complexity | Cost |
|--------|----------|------------|------|
| Local Development | Testing, demos | Low | Free |
| Docker | Consistent environments | Medium | Low |
| AWS ECS/Fargate | Scalable production | High | Medium-High |
| Azure Container Apps | Azure ecosystem | Medium | Medium |
| GCP Cloud Run | Serverless containers | Medium | Low-Medium |
| Traditional VPS | Simple deployments | Low | Low |

---

## Local Development Deployment

### Quick Start

```bash
# Install dependencies
curl -LsSf https://astral.sh/uv/install.sh | sh
npm install

# Set environment variables
export OPENAI_API_KEY="sk-proj-..."
export VITE_CHATKIT_API_DOMAIN_KEY="your-key"

# Start services
npm start
```

### Separate Services

```bash
# Terminal 1 - Backend
npm run backend
# Runs: uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
npm run frontend
# Runs: vite dev server on port 5170
```

---

## Docker Deployment

### Dockerfile (Backend)

```dockerfile
# app/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy requirements
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Dockerfile (Frontend)

```dockerfile
# Dockerfile.frontend
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source
COPY . .

# Build
RUN npm run build

# Production image
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: app/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - KNOWLEDGE_VECTOR_STORE_ID=${KNOWLEDGE_VECTOR_STORE_ID}
    restart: unless-stopped

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    environment:
      - VITE_CHATKIT_API_DOMAIN_KEY=${VITE_CHATKIT_API_DOMAIN_KEY}
    depends_on:
      - backend
    restart: unless-stopped
```

### Deploy with Docker Compose

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## AWS Deployment

### AWS ECS with Fargate

#### 1. Create ECR Repositories

```bash
# Create repositories
aws ecr create-repository --repository-name chatkit-backend
aws ecr create-repository --repository-name chatkit-frontend

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com
```

#### 2. Build and Push Images

```bash
# Build backend
docker build -t chatkit-backend -f app/Dockerfile .
docker tag chatkit-backend:latest \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com/chatkit-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/chatkit-backend:latest

# Build frontend
docker build -t chatkit-frontend -f Dockerfile.frontend .
docker tag chatkit-frontend:latest \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com/chatkit-frontend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/chatkit-frontend:latest
```

#### 3. Create ECS Task Definition

```json
{
  "family": "chatkit-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/chatkit-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "OPENAI_API_KEY",
          "value": "sk-proj-..."
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/chatkit",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "backend"
        }
      }
    },
    {
      "name": "frontend",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/chatkit-frontend:latest",
      "portMappings": [
        {
          "containerPort": 80,
          "protocol": "tcp"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/chatkit",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "frontend"
        }
      }
    }
  ]
}
```

#### 4. Create ECS Service

```bash
aws ecs create-service \
  --cluster chatkit-cluster \
  --service-name chatkit-service \
  --task-definition chatkit-task \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=frontend,containerPort=80"
```

---

## Azure Deployment

### Azure Container Apps

#### 1. Create Container Registry

```bash
az acr create \
  --resource-group chatkit-rg \
  --name chatkitregistry \
  --sku Basic

az acr login --name chatkitregistry
```

#### 2. Build and Push

```bash
# Build and push backend
docker build -t chatkitregistry.azurecr.io/chatkit-backend:latest -f app/Dockerfile .
docker push chatkitregistry.azurecr.io/chatkit-backend:latest

# Build and push frontend
docker build -t chatkitregistry.azurecr.io/chatkit-frontend:latest -f Dockerfile.frontend .
docker push chatkitregistry.azurecr.io/chatkit-frontend:latest
```

#### 3. Create Container App

```bash
az containerapp create \
  --name chatkit-app \
  --resource-group chatkit-rg \
  --environment chatkit-env \
  --image chatkitregistry.azurecr.io/chatkit-backend:latest \
  --target-port 8000 \
  --ingress external \
  --env-vars OPENAI_API_KEY=secretref:openai-key \
  --secrets openai-key="sk-proj-..." \
  --cpu 0.5 \
  --memory 1.0Gi
```

---

## GCP Deployment

### Google Cloud Run

#### 1. Build and Push to GCR

```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Build and push backend
docker build -t gcr.io/project-id/chatkit-backend:latest -f app/Dockerfile .
docker push gcr.io/project-id/chatkit-backend:latest

# Build and push frontend
docker build -t gcr.io/project-id/chatkit-frontend:latest -f Dockerfile.frontend .
docker push gcr.io/project-id/chatkit-frontend:latest
```

#### 2. Deploy to Cloud Run

```bash
# Deploy backend
gcloud run deploy chatkit-backend \
  --image gcr.io/project-id/chatkit-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=sk-proj-...

# Deploy frontend
gcloud run deploy chatkit-frontend \
  --image gcr.io/project-id/chatkit-frontend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## Traditional VPS Deployment

### Setup on Ubuntu Server

```bash
# 1. Install dependencies
sudo apt update
sudo apt install -y python3.11 python3-pip nodejs npm nginx

# 2. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Clone repository
git clone https://github.com/your-org/chatkit-app.git
cd chatkit-app

# 4. Install Python dependencies
uv pip install -r requirements.txt

# 5. Install Node dependencies
npm install

# 6. Build frontend
npm run build

# 7. Configure systemd service for backend
sudo tee /etc/systemd/system/chatkit-backend.service > /dev/null <<EOF
[Unit]
Description=ChatKit Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/chatkit-app
Environment="OPENAI_API_KEY=sk-proj-..."
ExecStart=/home/ubuntu/.local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 8. Start backend service
sudo systemctl daemon-reload
sudo systemctl enable chatkit-backend
sudo systemctl start chatkit-backend

# 9. Configure nginx
sudo tee /etc/nginx/sites-available/chatkit > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /home/ubuntu/chatkit-app/dist;
        try_files \$uri \$uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

# 10. Enable nginx site
sudo ln -s /etc/nginx/sites-available/chatkit /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Environment Variables Management

### Development (.env file)

```bash
# .env
OPENAI_API_KEY=sk-proj-...
KNOWLEDGE_VECTOR_STORE_ID=vs_...
VITE_CHATKIT_API_DOMAIN_KEY=your-key
```

### Production (Secrets Management)

#### AWS Secrets Manager

```bash
# Store secret
aws secretsmanager create-secret \
  --name chatkit/openai-key \
  --secret-string "sk-proj-..."

# Retrieve in application
import boto3
client = boto3.client('secretsmanager')
response = client.get_secret_value(SecretId='chatkit/openai-key')
api_key = response['SecretString']
```

#### Azure Key Vault

```bash
# Store secret
az keyvault secret set \
  --vault-name chatkit-vault \
  --name openai-key \
  --value "sk-proj-..."

# Retrieve in application
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

client = SecretClient(vault_url="https://chatkit-vault.vault.azure.net/",
                      credential=DefaultAzureCredential())
api_key = client.get_secret("openai-key").value
```

#### GCP Secret Manager

```bash
# Store secret
echo -n "sk-proj-..." | gcloud secrets create openai-key --data-file=-

# Retrieve in application
from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()
name = "projects/project-id/secrets/openai-key/versions/latest"
response = client.access_secret_version(request={"name": name})
api_key = response.payload.data.decode("UTF-8")
```

---

## Monitoring and Logging

### Application Logging

```python
# app/main.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.post("/chat")
async def chat(request: ChatRequest):
    logger.info(f"Chat request received: thread_id={request.thread_id}")
    try:
        # ... chat logic ...
        logger.info(f"Chat response sent: thread_id={thread_id}")
        return response
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise
```

### Health Check Endpoint

```python
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
```

### Metrics Endpoint

```python
from prometheus_client import Counter, Histogram, generate_latest

chat_requests = Counter('chat_requests_total', 'Total chat requests')
chat_duration = Histogram('chat_duration_seconds', 'Chat request duration')

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type="text/plain")
```

---

## Scaling Considerations

### Horizontal Scaling

- Use load balancer (ALB, Azure Load Balancer, GCP Load Balancer)
- Run multiple backend instances
- Share state via Redis or database
- Use sticky sessions for thread continuity

### Vertical Scaling

- Increase CPU/memory for containers
- Optimize database queries
- Implement caching (Redis, Memcached)
- Use connection pooling

### Auto-scaling Configuration

#### AWS ECS

```bash
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/chatkit-cluster/chatkit-service \
  --min-capacity 2 \
  --max-capacity 10

aws application-autoscaling put-scaling-policy \
  --policy-name chatkit-cpu-scaling \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/chatkit-cluster/chatkit-service \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

---

## Production Checklist

- [ ] Environment variables configured securely
- [ ] Secrets stored in secrets manager (not in code)
- [ ] HTTPS enabled with valid SSL certificate
- [ ] CORS configured correctly
- [ ] Rate limiting implemented
- [ ] Logging configured
- [ ] Monitoring and alerting set up
- [ ] Health check endpoint implemented
- [ ] Auto-scaling configured
- [ ] Backup strategy defined
- [ ] Disaster recovery plan documented
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] Documentation updated
- [ ] CI/CD pipeline configured
