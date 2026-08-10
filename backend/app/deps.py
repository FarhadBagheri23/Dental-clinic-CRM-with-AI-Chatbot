from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from .db import get_db
from .security import read_token

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
