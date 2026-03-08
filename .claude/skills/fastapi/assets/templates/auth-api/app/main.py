from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_db_and_tables
from app.routers import items, users, auth

app = FastAPI(
    title="FastAPI Auth Demo",
    version="0.1.0",
    description="A demo of a FastAPI application with authentication and authorization"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(items.router)
app.include_router(users.router)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI Auth Demo API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}