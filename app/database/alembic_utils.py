import os

DEFAULT_DATABASE_URL = "sqlite:///./app/app.db"


def get_migration_database_url() -> str:
    _load_dotenv()
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    try:
        from app.config import get_settings
    except Exception:
        return DEFAULT_DATABASE_URL
    return get_settings().database_url


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except Exception:
        return
    load_dotenv()
