# Authentication & Security

OAuth2, JWT, password hashing, and security best practices for FastAPI.

## Password Hashing

### Setup

```bash
pip install passlib[bcrypt] python-jose[cryptography]
```

```python
# app/auth/security.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

## JWT Tokens

### Token Generation

```python
# app/auth/security.py
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt

SECRET_KEY = "your-secret-key-keep-it-secret"  # Use environment variable!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

### Token Validation

```python
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
```

## OAuth2 with Password Flow

### Models

```python
# app/models.py
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = True

class UserCreate(SQLModel):
    username: str
    email: str
    password: str

class UserPublic(SQLModel):
    id: int
    username: str
    email: str
    is_active: bool

class Token(SQLModel):
    access_token: str
    token_type: str
```

### Login Endpoint

```python
# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select

router = APIRouter(tags=["auth"])

@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: SessionDep = Depends()
):
    # Find user
    statement = select(User).where(User.username == form_data.username)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()

    # Verify credentials
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")
```

### Register Endpoint

```python
@router.post("/register", response_model=UserPublic)
async def register(user: UserCreate, session: SessionDep):
    # Check if user exists
    statement = select(User).where(User.username == user.username)
    result = await session.execute(statement)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )

    # Create user
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password)
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)

    return db_user
```

## Protected Routes

### Get Current User Dependency

```python
# app/auth/dependencies.py
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import select

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: SessionDep
) -> User:
    username = decode_access_token(token)

    statement = select(User).where(User.username == username)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Type alias
CurrentUser = Annotated[User, Depends(get_current_active_user)]
```

### Using Protected Routes

```python
# app/routers/users.py
from app.auth.dependencies import CurrentUser

@router.get("/users/me", response_model=UserPublic)
async def read_users_me(current_user: CurrentUser):
    return current_user

@router.put("/users/me", response_model=UserPublic)
async def update_user_me(
    user_update: UserUpdate,
    current_user: CurrentUser,
    session: SessionDep
):
    # Update current user
    for key, value in user_update.model_dump(exclude_unset=True).items():
        setattr(current_user, key, value)

    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user
```

## API Key Authentication

### Simple API Key

```python
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY = "your-api-key"  # Use environment variable!
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
    return api_key

@router.get("/protected/")
async def protected_route(api_key: str = Depends(verify_api_key)):
    return {"message": "Access granted"}
```

### Database-Backed API Keys

```python
class APIKey(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(unique=True, index=True)
    user_id: int = Field(foreign_key="user.id")
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

async def verify_api_key(
    api_key: str = Security(api_key_header),
    session: SessionDep = Depends()
):
    statement = select(APIKey).where(
        APIKey.key == api_key,
        APIKey.is_active == True
    )
    result = await session.execute(statement)
    db_key = result.scalar_one_or_none()

    if not db_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or inactive API Key"
        )
    return db_key
```

## Role-Based Access Control (RBAC)

```python
from enum import Enum

class Role(str, Enum):
    USER = "user"
    ADMIN = "admin"

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str
    hashed_password: str
    role: Role = Field(default=Role.USER)

def require_role(required_role: Role):
    async def role_checker(current_user: CurrentUser):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# Usage
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(require_role(Role.ADMIN)),
    session: SessionDep = Depends()
):
    # Only admins can delete users
    pass
```

## CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Production (more restrictive)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

## Security Best Practices

### Environment Variables

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = {
        "env_file": ".env"
    }

settings = Settings()
```

```bash
# .env
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Generate Secure Secret Key

```python
import secrets

# Generate a secure random secret key
secret_key = secrets.token_urlsafe(32)
print(secret_key)
```

### Security Checklist

- [ ] Use HTTPS in production
- [ ] Store secrets in environment variables
- [ ] Hash passwords (never store plain text)
- [ ] Use strong secret keys (32+ bytes)
- [ ] Set appropriate token expiration
- [ ] Validate all user input
- [ ] Use CORS restrictively in production
- [ ] Implement rate limiting
- [ ] Log authentication attempts
- [ ] Use secure session management
- [ ] Implement account lockout after failed attempts
- [ ] Add CSRF protection for web forms
- [ ] Sanitize error messages (don't leak info)

## Common Patterns

### Refresh Tokens

```python
def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/refresh")
async def refresh_token(refresh_token: str):
    username = decode_access_token(refresh_token)
    access_token = create_access_token(data={"sub": username})
    return {"access_token": access_token, "token_type": "bearer"}
```

### Password Reset

```python
@router.post("/password-reset-request")
async def request_password_reset(email: str, session: SessionDep):
    user = await get_user_by_email(email, session)
    if user:
        reset_token = create_access_token(
            data={"sub": user.username, "type": "reset"},
            expires_delta=timedelta(hours=1)
        )
        # Send email with reset_token
        # await send_reset_email(user.email, reset_token)
    return {"message": "If email exists, reset link sent"}

@router.post("/password-reset")
async def reset_password(
    token: str,
    new_password: str,
    session: SessionDep
):
    username = decode_access_token(token)
    user = await get_user_by_username(username, session)
    user.hashed_password = get_password_hash(new_password)
    await session.commit()
    return {"message": "Password reset successful"}
```
