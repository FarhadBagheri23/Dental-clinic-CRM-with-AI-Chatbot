"""ASGI entrypoint. Wiring only — no endpoints live here."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import api_router
from app.core import throttle
from app.core.config import settings
from app.db.mongodb import close_db, get_db

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # The login throttle relies on a TTL index to expire its own records.
    # Failure to create it must not stop the API booting — a database that is
    # still starting up is the common case — but it has to be loud, because
    # without the index lockouts would never expire.
    try:
        await throttle.ensure_indexes(get_db())
    except Exception as e:
        log.warning("could not create login-throttle indexes: %s", e)
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
