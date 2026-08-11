"""The tool-calling loop.

ponytail: no LangGraph. What it buys — checkpointing, branching, `interrupt()`
before a write — is worth having the day write tools exist. Today every tool
is read-only, so the whole agent is "call the model, run any tools it asked
for, call it again", which is the fifty lines below. A graph framework here
would be a dependency tree wrapped around a while-loop.

When booking and registration land, this is the seam to revisit: the write
tools need a confirmation step, and that is the point where LangGraph's
`interrupt()` earns its place.
"""

import asyncio
import inspect
import json
import logging
from dataclasses import dataclass, field
from typing import Any

from openai import APIError, AsyncOpenAI

from app.agent.prompts import RESTRICTED_SUFFIX, SYSTEM_PROMPT
from app.agent.tools import TOOL_NAMES, Toolbox
from app.core.config import settings

log = logging.getLogger(__name__)

# A question needing more hops than this is a loop, not a query. Each hop is a
# billed round trip, so the cap is a cost control as much as a safety one.
MAX_STEPS = 6
TOOL_TIMEOUT_SECONDS = 20


def _schema_for(method) -> dict:
    """Builds an OpenAI function schema from the method's own signature.

    Hand-maintained JSON schemas drift from the code they describe, and the
    drift is invisible until the model passes an argument that no longer
    exists. The signature is the single source of truth.
    """
    hints = inspect.signature(method)
    props, required = {}, []
    for name, param in hints.parameters.items():
        if name == "self":
            continue
        annotation = param.annotation
        is_int = annotation in (int, "int") or "int" in str(annotation)
        props[name] = {"type": "integer" if is_int else "string"}
        if param.default is inspect.Parameter.empty:
            required.append(name)

    return {
        "type": "function",
        "function": {
            "name": method.__name__,
            # The docstring is what the model reads to choose a tool, so it is
            # written in Persian for the same reason the prompt is.
            "description": inspect.getdoc(method) or "",
            "parameters": {"type": "object", "properties": props, "required": required},
        },
    }


@dataclass
class Answer:
    text: str
    tools_used: list[str] = field(default_factory=list)
    steps: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0


class Assistant:
    def __init__(self, toolbox: Toolbox, *, owner: bool = True):
        self.toolbox = toolbox
        self.owner = owner
        self.client = AsyncOpenAI(
            api_key=settings.avalai_api_key,
            base_url=settings.avalai_base_url,
            timeout=90,
            max_retries=2,
        )
        self.schemas = [_schema_for(getattr(toolbox, n)) for n in TOOL_NAMES]

    def _system(self) -> str:
        return SYSTEM_PROMPT if self.owner else SYSTEM_PROMPT + RESTRICTED_SUFFIX

    async def _run_tool(self, name: str, raw_args: str) -> dict:
        """Runs one tool. Never raises: a tool failure must reach the model as
        a message it can recover from, not a 500 the owner sees."""
        if name not in TOOL_NAMES:
            return {"error": f"ابزار ناشناخته: {name}"}
        try:
            args = json.loads(raw_args or "{}")
        except json.JSONDecodeError:
            return {"error": "آرگومان‌ها JSON معتبر نبودند."}

        try:
            return await asyncio.wait_for(
                getattr(self.toolbox, name)(**args), timeout=TOOL_TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            log.warning("tool %s timed out", name)
            return {"error": "محاسبه طول کشید؛ بازه کوچک‌تری را امتحان کن."}
        except TypeError as e:
            return {"error": f"پارامتر نادرست: {e}"}
        except ValueError as e:
            # period.resolve() raises this for an unknown month name, and its
            # message is already written for the model to act on.
            return {"error": str(e)}
        except Exception:
            log.exception("tool %s failed", name)
            return {"error": "اجرای ابزار با خطا مواجه شد."}

    async def ask(self, question: str, history: list[dict] | None = None) -> Answer:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._system()},
            *(history or []),
            {"role": "user", "content": question},
        ]
        answer = Answer(text="")

        for step in range(1, MAX_STEPS + 1):
            try:
                response = await self.client.chat.completions.create(
                    model=settings.avalai_model,
                    messages=messages,
                    tools=self.schemas,
                    temperature=0.2,   # numbers and citations, not prose variety
                )
            except APIError as e:
                log.error("avalai call failed: %s", e)
                answer.text = "ارتباط با سرویس هوش مصنوعی برقرار نشد. دوباره تلاش کنید."
                return answer

            if response.usage:
                answer.prompt_tokens += response.usage.prompt_tokens
                answer.completion_tokens += response.usage.completion_tokens

            message = response.choices[0].message
            answer.steps = step

            if not message.tool_calls:
                answer.text = (message.content or "").strip()
                return answer

            # The assistant turn must be replayed verbatim, tool_calls and all,
            # or the follow-up tool messages have nothing to attach to.
            messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {"id": c.id, "type": "function",
                     "function": {"name": c.function.name, "arguments": c.function.arguments}}
                    for c in message.tool_calls
                ],
            })

            results = await asyncio.gather(*[
                self._run_tool(c.function.name, c.function.arguments)
                for c in message.tool_calls
            ])
            for call, result in zip(message.tool_calls, results):
                answer.tools_used.append(call.function.name)
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })

        answer.text = "نتوانستم به پاسخ قطعی برسم. لطفاً پرسش را دقیق‌تر بپرسید."
        return answer
