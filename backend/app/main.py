from fastapi import FastAPI

from app.api.routes import health, resorts, roads
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
    )

    @app.get("/", tags=["root"])
    def root() -> dict[str, str]:
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "docs": "/docs",
            "health": "/health",
        }

    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(resorts.router, prefix="/resorts", tags=["resorts"])
    app.include_router(roads.router, prefix="/roads", tags=["roads"])

    return app


app = create_app()
