# FastAPI CRUD Demo

A complete FastAPI application demonstrating CRUD operations with SQLModel and PostgreSQL.

## Features

- RESTful API with full CRUD operations
- SQLModel database integration
- PostgreSQL database connection
- Environment variable configuration
- Automatic API documentation
- Proper error handling

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL database
- Docker (optional, for containerized deployment)

### Installation

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

5. Run database migrations:
```bash
# Create database tables
python -c "from app.database import create_db_and_tables; create_db_and_tables()"
```

### Running the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### API Documentation

- OpenAPI docs: http://localhost:8000/docs
- ReDoc docs: http://localhost:8000/redoc

## Endpoints

### Items
- `GET /items/` - List all items
- `POST /items/` - Create a new item
- `GET /items/{item_id}` - Get a specific item
- `PUT /items/{item_id}` - Update an item
- `DELETE /items/{item_id}` - Delete an item

### Users
- `GET /users/` - List all users
- `POST /users/` - Create a new user
- `GET /users/{user_id}` - Get a specific user
- `PUT /users/{user_id}` - Update a user
- `DELETE /users/{user_id}` - Delete a user

## Project Structure

```
app/
├── main.py          # Main application entry point
├── config.py        # Configuration management
├── database.py      # Database connection and session management
├── models.py        # SQLModel database models
├── schemas.py       # Pydantic request/response models
├── routers/         # API route handlers
│   ├── __init__.py
│   ├── items.py     # Items endpoints
│   └── users.py     # Users endpoints
```

## Deployment

### Docker

```bash
# Build image
docker build -t fastapi-crud-demo .

# Run container
docker run -d -p 8000:8000 --env-file .env fastapi-crud-demo
```

### Production

For production deployment, ensure:
- Use a production WSGI server (Gunicorn, Uvicorn workers)
- Configure proper database connection pooling
- Set appropriate security headers
- Use HTTPS in production