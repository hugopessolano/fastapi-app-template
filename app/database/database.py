from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

settings = get_settings()
DATABASE_URL = settings.database_url

connect_args = {}
try:
    backend = make_url(DATABASE_URL).get_backend_name()
    if backend == "sqlite":
        connect_args = {"check_same_thread": False, "timeout": 30}
except Exception:
    # If inspection fails, fall back to default behavior.
    pass

engine_kwargs = {"connect_args": connect_args} if connect_args else {}
engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Session = sessionmaker(engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

