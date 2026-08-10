from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import client
from .routers import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    client.close()


app = FastAPI(
    title="Dental Clinic BI API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# Only needed for the Vite dev server on a different port. In production
# nginx serves the SPA and proxies /api, so requests are same-origin.
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,  # required for the session cookie
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth.router, prefix="/api")


@app.get("/api/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok"}
