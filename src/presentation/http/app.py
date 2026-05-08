from fastapi import FastAPI

from infrastructure.settings import get_settings
from presentation.http.routes import health


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version)

    app.include_router(health.router)

    return app
