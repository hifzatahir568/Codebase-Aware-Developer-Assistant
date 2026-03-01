from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes.filesystem import router as filesystem_router
from app.api.routes.health import router as health_router
from app.api.routes.projects import router as projects_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.rate_limit import RateLimitMiddleware
from app.db.database import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title=settings.app_title, lifespan=lifespan)

    if settings.frontend_dir.exists():
        app.mount("/app", StaticFiles(directory=str(settings.frontend_dir), html=True), name="frontend")

    app.add_middleware(RateLimitMiddleware)
    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(filesystem_router)
    app.include_router(projects_router)

    return app


app = create_app()
