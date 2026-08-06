from fastapi import FastAPI

from app.api.routes import health, resorts, roads, weather
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        root_path="/api",
    )

    @app.get("/", tags=["root"])
    def root() -> dict[str, str]:
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "docs": "/api/docs",
            "health": "/api/health",
        }

    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(resorts.router, prefix="/resorts", tags=["resorts"])
    app.include_router(roads.router, prefix="/roads", tags=["roads"])
    app.include_router(weather.router, prefix="/weather", tags=["weather"])

    return app


app = create_app()
