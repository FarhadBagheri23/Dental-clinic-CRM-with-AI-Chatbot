from typing import Literal

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    # Trimmed server-side: every turn is re-sent and re-billed, and a client
    # that never truncates would grow the prompt without limit.
    history: list[ChatTurn] = Field(default_factory=list, max_length=12)


class ChatReply(BaseModel):
    reply: str
    # Surfaced so the owner can see which report an answer came from and
    # check it against that page — the assistant's numbers are only
    # trustworthy if they are traceable.
    tools_used: list[str] = Field(default_factory=list)
    steps: int = 0
    tokens: int = 0
