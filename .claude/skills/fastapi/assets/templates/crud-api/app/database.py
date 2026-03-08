from sqlmodel import create_engine, SQLModel, Session
from app.config import settings

# Create engine
engine = create_engine(settings.database_url, echo=settings.debug)

def create_db_and_tables():
    """Create all database tables"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Dependency to get database session"""
    with Session(engine) as session:
        yield session

# Type alias for dependency injection
SessionDep = Session