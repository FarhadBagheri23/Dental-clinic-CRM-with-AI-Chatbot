"""Aggregates every router into a single api_router.

main.py includes only this, so adding an endpoint group means adding one
import and one include_router line here — main.py never changes.
"""

from fastapi import APIRouter

from app.api.routers import auth, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
