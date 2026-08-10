"""Shared FastAPI dependencies.

Endpoints annotate parameters with the aliases below rather than calling
Depends() inline, so a change to how the database or the current user is
resolved happens in one place.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.security import read_token
from app.db.mongodb import get_db

SESSION_COOKIE = "clinic_session"

Database = Annotated[AsyncIOMotorDatabase, Depends(get_db)]


def current_user(request: Request) -> dict:
    claims = read_token(request.cookies.get(SESSION_COOKIE))
    if claims is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="برای دسترسی به این بخش وارد شوید.",
        )
    return claims


CurrentUser = Annotated[dict, Depends(current_user)]
