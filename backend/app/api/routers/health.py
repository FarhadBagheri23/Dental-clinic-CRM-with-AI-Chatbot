from fastapi import APIRouter

from app.db.mongodb import client

router = APIRouter(tags=["meta"])


@router.get("/health")
async def health() -> dict:
    """Liveness only — deliberately does not touch Mongo, so the container
    stays healthy while the database is still starting."""
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict:
    """Readiness — fails while Mongo is unreachable."""
    await client.admin.command("ping")
    return {"status": "ready"}
