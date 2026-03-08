# Database Integration with SQLModel

SQLModel patterns for FastAPI with PostgreSQL (Neon Serverless).

## SQLModel Basics

SQLModel combines SQLAlchemy and Pydantic - use it for both database tables and API schemas.

### Model Pattern

```python
from sqlmodel import SQLModel, Field, Relationship

# Base model with shared fields
class HeroBase(SQLModel):
    name: str = Field(index=True)
    secret_name: str
    age: int | None = Field(default=None, index=True)

# Table model (stored in database)
class Hero(HeroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    team_id: int | None = Field(default=None, foreign_key="team.id")

    # Relationships
    team: "Team | None" = Relationship(back_populates="heroes")

# API schemas
class HeroCreate(HeroBase):
    pass

class HeroPublic(HeroBase):
    id: int

class HeroUpdate(SQLModel):
    name: str | None = None
    secret_name: str | None = None
    age: int | None = None
    team_id: int | None = None
```

## Database Connection

### Neon Serverless PostgreSQL Setup

```python
# app/database.py
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Neon connection string format
# postgresql://[user]:[password]@[endpoint]/[database]?sslmode=require
DATABASE_URL = "postgresql://user:password@ep-example-123456.us-east-2.aws.neon.tech/neondb?sslmode=require"

# For async (recommended)
async_engine = create_async_engine(
    DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=True,  # Set to False in production
    future=True
)

# For sync (simpler but blocks)
sync_engine = create_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"sslmode": "require"}
)
```

### Environment Variables

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    echo_sql: bool = False

    model_config = {
        "env_file": ".env"
    }

settings = Settings()
```

```bash
# .env
DATABASE_URL=postgresql://user:password@ep-example.neon.tech/neondb?sslmode=require
ECHO_SQL=false
```

### Create Tables

```python
# app/database.py
async def create_db_and_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

# app/main.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_db_and_tables()
    yield
    # Shutdown (cleanup if needed)

app = FastAPI(lifespan=lifespan)
```

## Session Management

### Async Session Dependency

```python
# app/database.py
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

async_session_maker = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_session():
    async with async_session_maker() as session:
        yield session

# Type alias for dependency injection
SessionDep = Annotated[AsyncSession, Depends(get_session)]
```

### Sync Session Dependency (Simpler)

```python
def get_session():
    with Session(sync_engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
```

## CRUD Operations

### Create

```python
from sqlmodel import select

@app.post("/heroes/", response_model=HeroPublic)
async def create_hero(hero: HeroCreate, session: SessionDep):
    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    await session.commit()
    await session.refresh(db_hero)
    return db_hero
```

### Read (Single)

```python
@app.get("/heroes/{hero_id}", response_model=HeroPublic)
async def read_hero(hero_id: int, session: SessionDep):
    hero = await session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero
```

### Read (List with Pagination)

```python
@app.get("/heroes/", response_model=list[HeroPublic])
async def read_heroes(
    session: SessionDep,
    offset: int = 0,
    limit: int = Query(default=100, le=100)
):
    result = await session.execute(
        select(Hero).offset(offset).limit(limit)
    )
    heroes = result.scalars().all()
    return heroes
```

### Update

```python
@app.patch("/heroes/{hero_id}", response_model=HeroPublic)
async def update_hero(
    hero_id: int,
    hero_update: HeroUpdate,
    session: SessionDep
):
    db_hero = await session.get(Hero, hero_id)
    if not db_hero:
        raise HTTPException(status_code=404, detail="Hero not found")

    # Update only provided fields
    hero_data = hero_update.model_dump(exclude_unset=True)
    for key, value in hero_data.items():
        setattr(db_hero, key, value)

    session.add(db_hero)
    await session.commit()
    await session.refresh(db_hero)
    return db_hero
```

### Delete

```python
@app.delete("/heroes/{hero_id}")
async def delete_hero(hero_id: int, session: SessionDep):
    hero = await session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")

    await session.delete(hero)
    await session.commit()
    return {"ok": True}
```

## Relationships

### One-to-Many

```python
class Team(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    headquarters: str

    heroes: list["Hero"] = Relationship(back_populates="team")

class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    team_id: int | None = Field(default=None, foreign_key="team.id")

    team: Team | None = Relationship(back_populates="heroes")
```

### Querying with Relationships

```python
from sqlmodel import select
from sqlalchemy.orm import selectinload

@app.get("/teams/{team_id}", response_model=TeamPublic)
async def read_team_with_heroes(team_id: int, session: SessionDep):
    statement = select(Team).where(Team.id == team_id).options(
        selectinload(Team.heroes)
    )
    result = await session.execute(statement)
    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team
```

## Advanced Queries

### Filtering

```python
@app.get("/heroes/search/", response_model=list[HeroPublic])
async def search_heroes(
    session: SessionDep,
    name: str | None = None,
    min_age: int | None = None
):
    statement = select(Hero)

    if name:
        statement = statement.where(Hero.name.contains(name))
    if min_age:
        statement = statement.where(Hero.age >= min_age)

    result = await session.execute(statement)
    heroes = result.scalars().all()
    return heroes
```

### Ordering

```python
@app.get("/heroes/", response_model=list[HeroPublic])
async def read_heroes(
    session: SessionDep,
    order_by: Literal["name", "age"] = "name"
):
    if order_by == "name":
        statement = select(Hero).order_by(Hero.name)
    else:
        statement = select(Hero).order_by(Hero.age.desc())

    result = await session.execute(statement)
    return result.scalars().all()
```

### Aggregation

```python
from sqlalchemy import func

@app.get("/heroes/stats/")
async def get_hero_stats(session: SessionDep):
    statement = select(
        func.count(Hero.id).label("total"),
        func.avg(Hero.age).label("avg_age"),
        func.max(Hero.age).label("max_age")
    )
    result = await session.execute(statement)
    stats = result.one()

    return {
        "total": stats.total,
        "avg_age": stats.avg_age,
        "max_age": stats.max_age
    }
```

## Transactions

### Manual Transaction Control

```python
@app.post("/transfer/")
async def transfer_hero(
    hero_id: int,
    new_team_id: int,
    session: SessionDep
):
    try:
        hero = await session.get(Hero, hero_id)
        if not hero:
            raise HTTPException(status_code=404, detail="Hero not found")

        new_team = await session.get(Team, new_team_id)
        if not new_team:
            raise HTTPException(status_code=404, detail="Team not found")

        hero.team_id = new_team_id
        session.add(hero)
        await session.commit()

        return {"ok": True}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
```

## Error Handling

### Database Errors

```python
from sqlalchemy.exc import IntegrityError

@app.post("/heroes/", response_model=HeroPublic)
async def create_hero(hero: HeroCreate, session: SessionDep):
    try:
        db_hero = Hero.model_validate(hero)
        session.add(db_hero)
        await session.commit()
        await session.refresh(db_hero)
        return db_hero
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=400,
            detail="Hero with this name already exists"
        )
```

## Migrations

### Alembic Setup

```bash
pip install alembic
alembic init alembic
```

```python
# alembic/env.py
from app.models import SQLModel
from app.database import DATABASE_URL

config.set_main_option("sqlalchemy.url", DATABASE_URL)
target_metadata = SQLModel.metadata
```

```bash
# Create migration
alembic revision --autogenerate -m "Add heroes table"

# Apply migration
alembic upgrade head
```

## Best Practices

1. **Always use async with Neon**: Neon is optimized for serverless/async
2. **One session per request**: Use dependency injection
3. **Close sessions properly**: Use `yield` in dependencies
4. **Use transactions**: Wrap multi-step operations
5. **Index frequently queried fields**: Add `index=True` to Field
6. **Eager load relationships**: Use `selectinload()` to avoid N+1 queries
7. **Validate before commit**: Use Pydantic models
8. **Handle errors gracefully**: Catch IntegrityError, rollback on failure
