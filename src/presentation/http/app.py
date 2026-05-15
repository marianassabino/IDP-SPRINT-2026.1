from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from infrastructure.settings import get_settings
from presentation.http.routes import health
from presentation.http.routes.auth import router as auth_router
from presentation.http.routes.projects import router as projects_router
from presentation.http.routes.users import router as users_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version)


    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(health.router)
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(projects_router)

    return app
