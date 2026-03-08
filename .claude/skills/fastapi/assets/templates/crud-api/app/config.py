from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    database_url: str

    # App
    app_name: str = "FastAPI CRUD Demo"
    debug: bool = False

    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }

@lru_cache
def get_settings():
    return Settings()

settings = get_settings()