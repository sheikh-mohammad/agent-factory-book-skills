# FastAPI Auth Demo

A complete FastAPI application demonstrating authentication and authorization with SQLModel and PostgreSQL.

## Features

- User registration and authentication
- JWT token-based authentication
- Password hashing with bcrypt
- Protected routes and dependencies
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
# Edit .env with your database credentials and secret key
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

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/token` - Login and get JWT token
- `GET /auth/me` - Get current user info (protected)
- `PUT /auth/me` - Update current user info (protected)

### Items
- `GET /items/` - List all items (protected)
- `POST /items/` - Create a new item (protected)
- `GET /items/{item_id}` - Get a specific item (protected)
- `PUT /items/{item_id}` - Update an item (protected)
- `DELETE /items/{item_id}` - Delete an item (protected)

### Users
- `GET /users/` - List all users (protected)
- `GET /users/{user_id}` - Get a specific user (protected)
- `PUT /users/{user_id}` - Update a user (protected)
- `DELETE /users/{user_id}` - Delete a user (protected)

## Project Structure

```
app/
├── main.py          # Main application entry point
├── config.py        # Configuration management
├── database.py      # Database connection and session management
├── models.py        # SQLModel database models
├── schemas.py       # Pydantic request/response models
├── auth/            # Authentication logic
│   ├── __init__.py
│   ├── security.py  # Password hashing and JWT
│   └── dependencies.py # Authentication dependencies
├── routers/         # API route handlers
│   ├── __init__.py
│   ├── items.py     # Items endpoints
│   ├── users.py     # Users endpoints
│   └── auth.py      # Authentication endpoints
```

## Authentication Flow

1. **Register**: POST `/auth/register` with username, email, password
2. **Login**: POST `/auth/token` with username and password
3. **Use token**: Include JWT token in Authorization header for protected endpoints
   ```
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

## Deployment

### Docker

```bash
# Build image
docker build -t fastapi-auth-demo .

# Run container
docker run -d -p 8000:8000 --env-file .env fastapi-auth-demo
```

### Production

For production deployment, ensure:
- Use a production WSGI server (Gunicorn, Uvicorn workers)
- Configure proper database connection pooling
- Set appropriate security headers
- Use HTTPS in production
- Rotate secret keys regularly