from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.auth.build_permissions import build_permissions
from app.config import get_settings
from app.database.database import engine
from app.database.models import Base
from app.initialization import initialize_database
from app.middleware import log_middleware, add_headers_middleware
from app.routers.registry import get_router_modules, load_routers
from app.views.views_creation import create_default_views


def create_app() -> FastAPI:
    settings = get_settings()
    Base.metadata.create_all(bind=engine)
    create_default_views()

    app = FastAPI()
    app.add_middleware(BaseHTTPMiddleware, dispatch=log_middleware)
    app.add_middleware(BaseHTTPMiddleware, dispatch=add_headers_middleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Next-Page", "X-Last-Page"],
    )

    router_modules = get_router_modules(settings.normalized_auth_mode)
    for router in load_routers(router_modules):
        app.include_router(router)

    if settings.auto_build_permissions:
        build_permissions(app)
    if settings.enable_seed_data:
        initialize_database(check_existing_users=settings.seed_check_existing_users)

    @app.get("/")
    async def root():
        return {"message": "Service Running"}

    return app


app = create_app()


