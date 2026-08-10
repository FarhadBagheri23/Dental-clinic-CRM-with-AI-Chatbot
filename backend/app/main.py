"""ASGI entrypoint. Wiring only — no endpoints live here."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import api_router
from app.core.config import settings
from app.db.mongodb import close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    close_db()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.project_name,
        version="1.0.0",
        lifespan=lifespan,
        docs_url=f"{settings.api_prefix}/docs",
        openapi_url=f"{settings.api_prefix}/openapi.json",
    )

    # Only needed for the Vite dev server on a different port. In production
    # nginx serves the SPA and proxies /api, so requests are same-origin and
    # this list is empty.
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,  # required for the session cookie
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
