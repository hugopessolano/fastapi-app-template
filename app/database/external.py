from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

settings = get_settings()
external_url = settings.external_database_url

ExternalSessionLocal = None

if external_url:
    connect_args = {}
    try:
        backend = make_url(external_url).get_backend_name()
        if backend == "sqlite":
            connect_args = {"check_same_thread": False, "timeout": 30}
    except Exception:
        connect_args = {}

    engine_kwargs = {"connect_args": connect_args} if connect_args else {}
    external_engine = create_engine(external_url, **engine_kwargs)
    ExternalSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=external_engine,
    )


def get_external_db() -> Generator:
    """
    Dependency to access an optional external database.
    Raises RuntimeError if EXTERNAL_DB_URL is not configured.
    """
    if ExternalSessionLocal is None:
        raise RuntimeError(
            "EXTERNAL_DB_URL is not configured. Set it in your .env to use get_external_db()."
        )
    db = ExternalSessionLocal()
    try:
        yield db
    finally:
        db.close()
