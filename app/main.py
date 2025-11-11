from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.models import Base
from app.database.database import engine
from app.views.views_creation import create_default_views
from app.routers import stores, roles, permissions, auth, users
from app.auth.build_permissions import build_permissions
from starlette.middleware.base import BaseHTTPMiddleware
from app.middleware import log_middleware, add_headers_middleware
from app.initialization import initialize_database
from app.config import get_settings

settings = get_settings()

Base.metadata.create_all(bind=engine)
create_default_views()

app = FastAPI()
app.add_middleware(BaseHTTPMiddleware,dispatch=log_middleware)
app.add_middleware(BaseHTTPMiddleware,dispatch=add_headers_middleware)

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
    expose_headers=["X-Next-Page", "X-Last-Page"],
)

app.include_router(stores.router)
app.include_router(roles.router)
app.include_router(permissions.router)
app.include_router(users.router)
app.include_router(auth.router)

if settings.auto_build_permissions:
    build_permissions(app)
if settings.enable_seed_data:
    initialize_database(check_existing_users=settings.seed_check_existing_users)

@app.get("/")
async def root():
    return {"message": "Service Running"}


