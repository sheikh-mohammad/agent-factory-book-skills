# FastAPI Core Concepts

Official FastAPI patterns for routing, request/response handling, dependency injection, and validation.

## Path Operations

### Basic Routing

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

@app.post("/items/")
async def create_item(item: Item):
    return item

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    return {"item_id": item_id, **item.dict()}

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    return {"deleted": item_id}
```

### HTTP Methods

- **GET**: Retrieve data (idempotent, cacheable)
- **POST**: Create new resources
- **PUT**: Replace entire resource
- **PATCH**: Partial update
- **DELETE**: Remove resource

## Request Parameters

### Path Parameters

```python
@app.get("/users/{user_id}/items/{item_id}")
async def read_user_item(user_id: int, item_id: str):
    return {"user_id": user_id, "item_id": item_id}
```

### Query Parameters

```python
from typing import Annotated
from fastapi import Query

@app.get("/items/")
async def read_items(
    skip: int = 0,
    limit: int = 10,
    q: str | None = None
):
    return {"skip": skip, "limit": limit, "q": q}

# With validation
@app.get("/items/")
async def read_items(
    q: Annotated[str | None, Query(min_length=3, max_length=50)] = None
):
    return {"q": q}
```

### Query Parameter Models (Pydantic)

```python
from pydantic import BaseModel, Field
from typing import Literal

class FilterParams(BaseModel):
    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []

@app.get("/items/")
async def read_items(filter_query: Annotated[FilterParams, Query()]):
    return filter_query
```

### Request Body

```python
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float = Field(gt=0)
    tax: float | None = None

@app.post("/items/")
async def create_item(item: Item):
    return item
```

## Response Models

### Basic Response Model

```python
class ItemResponse(BaseModel):
    id: int
    name: str
    price: float

@app.post("/items/", response_model=ItemResponse)
async def create_item(item: Item) -> ItemResponse:
    # Even if you return extra fields, only ItemResponse fields are returned
    return ItemResponse(id=1, name=item.name, price=item.price)
```

### Status Codes

```python
from fastapi import status

@app.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(item: Item):
    return item

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int):
    return None
```

### Multiple Response Models

```python
from fastapi import Response

@app.get("/items/{item_id}", responses={
    200: {"model": Item},
    404: {"description": "Item not found"}
})
async def read_item(item_id: int):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return items[item_id]
```

## Dependency Injection

### Basic Dependencies

```python
from fastapi import Depends

async def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}

@app.get("/items/")
async def read_items(commons: dict = Depends(common_parameters)):
    return commons

@app.get("/users/")
async def read_users(commons: dict = Depends(common_parameters)):
    return commons
```

### Dependencies with Yield

```python
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/items/")
async def read_items(db: Session = Depends(get_db)):
    return db.query(Item).all()
```

### Class-Based Dependencies

```python
class CommonQueryParams:
    def __init__(self, q: str | None = None, skip: int = 0, limit: int = 100):
        self.q = q
        self.skip = skip
        self.limit = limit

@app.get("/items/")
async def read_items(commons: CommonQueryParams = Depends()):
    return commons
```

### Router-Level Dependencies

```python
from fastapi import APIRouter, Depends

async def verify_token(token: str = Header(...)):
    if token != "secret-token":
        raise HTTPException(status_code=403)

router = APIRouter(
    prefix="/admin",
    dependencies=[Depends(verify_token)]
)

@router.get("/users/")
async def read_users():
    return [{"username": "admin"}]
```

### Application-Level Dependencies

```python
async def log_request():
    print("Request received")

app = FastAPI(dependencies=[Depends(log_request)])
```

## Validation

### Field Validation

```python
from pydantic import BaseModel, Field, EmailStr, validator

class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    age: int = Field(..., ge=0, le=120)

    @validator('username')
    def username_alphanumeric(cls, v):
        assert v.isalnum(), 'must be alphanumeric'
        return v
```

### Query Parameter Validation

```python
from typing import Annotated
from fastapi import Query

@app.get("/items/")
async def read_items(
    q: Annotated[str, Query(min_length=3, max_length=50, pattern="^[a-zA-Z]+$")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 10
):
    return {"q": q, "limit": limit}
```

## Error Handling

### HTTPException

```python
from fastapi import HTTPException

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    if item_id not in items:
        raise HTTPException(
            status_code=404,
            detail="Item not found",
            headers={"X-Error": "Custom header"}
        )
    return items[item_id]
```

### Custom Exception Handlers

```python
from fastapi import Request
from fastapi.responses import JSONResponse

class CustomException(Exception):
    def __init__(self, name: str):
        self.name = name

@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=418,
        content={"message": f"Oops! {exc.name} did something wrong."}
    )
```

### Validation Error Handler

```python
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return PlainTextResponse(str(exc), status_code=400)
```

## Routers

### Creating Routers

```python
from fastapi import APIRouter

router = APIRouter(
    prefix="/items",
    tags=["items"],
    responses={404: {"description": "Not found"}}
)

@router.get("/")
async def read_items():
    return [{"name": "Item 1"}]

@router.get("/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
```

### Including Routers

```python
from app.routers import items, users

app = FastAPI()

app.include_router(items.router)
app.include_router(users.router, prefix="/api/v1")
```

## Background Tasks

```python
from fastapi import BackgroundTasks

def write_log(message: str):
    with open("log.txt", mode="a") as log:
        log.write(message)

@app.post("/send-notification/")
async def send_notification(
    email: str,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(write_log, f"Notification sent to {email}\n")
    return {"message": "Notification sent"}
```

## WebSockets

```python
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")
```

### WebSocket with Dependencies

```python
async def get_token(token: str = Query(...)):
    if token != "secret-token":
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    return token

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    token: str = Depends(get_token)
):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Client {client_id}: {data}")
    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected")
```

## Middleware

### CORS Middleware

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Custom Middleware

```python
from fastapi import Request
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

## Async vs Sync

### When to Use Async

```python
# Use async for I/O operations
@app.get("/external-api")
async def call_external_api():
    response = await httpx_client.get("https://api.example.com")
    return response.json()

# Use async for database operations
@app.get("/users/")
async def read_users(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User))
    return result.scalars().all()
```

### When to Use Sync

```python
# Use sync for CPU-bound operations
@app.post("/process/")
def process_data(data: list[int]):
    # Heavy computation
    result = sum(x ** 2 for x in data)
    return {"result": result}

# Use sync for simple operations
@app.get("/health")
def health_check():
    return {"status": "ok"}
```
