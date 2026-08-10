from fastapi import APIRouter, HTTPException, Response, status
from starlette.concurrency import run_in_threadpool

from app.api.deps import SESSION_COOKIE, CurrentUser, Database
from app.core.config import settings
from app.core.security import DUMMY_HASH, create_token, verify_password
from app.schemas.auth import LoginRequest, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
        max_age=settings.session_ttl_hours * 3600,
    )


@router.post("/login", response_model=UserOut)
async def login(body: LoginRequest, response: Response, db: Database) -> UserOut:
    user = await db.users.find_one({"username": body.username.strip()})

    # Always hash, even for an unknown user, so both paths cost the same.
    # scrypt is deliberately slow (~100ms), which would block the event loop.
    stored = user["password_hash"] if user else DUMMY_HASH
    ok = await run_in_threadpool(verify_password, body.password, stored)

    if not user or not ok:
        # Deliberately identical for unknown user and wrong password.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نام کاربری یا رمز عبور نادرست است.",
        )

    _set_session_cookie(response, create_token(user))
    return UserOut(
        username=user["username"],
        name=user.get("display_name") or user["username"],
        role=user.get("role") or "کاربر",
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    return UserOut(username=user["sub"], name=user["name"], role=user["role"])
