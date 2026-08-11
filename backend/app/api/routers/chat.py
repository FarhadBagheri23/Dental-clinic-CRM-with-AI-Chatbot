from fastapi import APIRouter, HTTPException, status

from app.agent.assistant import Assistant
from app.agent.corpus import build_index
from app.agent.tools import Toolbox
from app.api.deps import CurrentUser, Database
from app.core.config import settings
from app.core.redaction import is_owner
from app.schemas.chat import ChatReply, ChatRequest

router = APIRouter(prefix="/chat", tags=["chat"])

# The corpus changes only when services, insurers or the flow docs change, so
# it is built once on first use rather than per request. Restarting the API
# reloads it, which is the right cadence for data that changes by deploy.
_index = None


async def _toolbox(db, *, owner: bool) -> Toolbox:
    global _index
    if _index is None:
        _index = await build_index(db)
    return Toolbox(db=db, index=_index, owner=owner)


@router.get("/status")
async def status_(user: CurrentUser) -> dict:
    """Whether the assistant is configured — lets the UI hide the tab instead
    of offering a chat that cannot answer.

    The upstream model id is deliberately not returned. Nothing in the panel
    needs it, and an endpoint that names the provider and model hands a probe
    the exact stack to look up known jailbreaks for.
    """
    return {"enabled": settings.assistant_enabled}


@router.post("", response_model=ChatReply)
async def ask(body: ChatRequest, db: Database, user: CurrentUser) -> ChatReply:
    if not settings.assistant_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="دستیار هوشمند پیکربندی نشده است.",
        )

    # Role drives what the assistant may disclose. Passing the claim through
    # rather than trusting the client means a restricted user cannot widen
    # their own access by editing a request body. The toolbox gets the same
    # flag, so a restricted user is never handed the sensitive fields in the
    # first place — the prompt only explains the refusal, it does not enforce it.
    owner = is_owner(user)
    assistant = Assistant(await _toolbox(db, owner=owner), owner=owner)
    answer = await assistant.ask(
        body.message,
        [m.model_dump() for m in body.history],
    )
    return ChatReply(
        reply=answer.text,
        tools_used=answer.tools_used,
        steps=answer.steps,
        tokens=answer.prompt_tokens + answer.completion_tokens,
    )
