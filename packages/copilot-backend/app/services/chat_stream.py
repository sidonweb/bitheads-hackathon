"""SSE formatter and async generator for streaming chat responses."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from ..agent.graph import chat_turn_stream
from ..agent.guardrails import AgentError, user_message_for
from ..db import engine
from ..sdui.pipeline import assemble_chat_blocks, is_viz_only_message
from ..sdui.schema import SDUI_VERSION

_SOFT_FAIL_CODES = frozenset(
    {"AGENT_TOOL_LIMIT", "AGENT_RECURSION_LIMIT", "AGENT_NO_DECISION"}
)


def format_sse(event_type: str, data: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


async def _yield_block_frames(
    exp: dict,
    *,
    message: str,
    reply: str,
    decision: dict | None,
    warning: dict | None,
    tool_calls_used: int,
) -> list[str]:
    with engine.begin() as conn:
        blocks = await assemble_chat_blocks(
            conn,
            exp,
            message=message,
            reply=reply,
            decision=decision,
            warning=warning,
            tool_calls_used=tool_calls_used,
        )
    return [format_sse("block", block) for block in blocks]


async def stream_chat_sse(
    exp: dict,
    message: str,
    session_id: str,
) -> AsyncIterator[str]:
    """Yield SSE frames for one chat turn. Always ends with done or error."""
    terminal_sent = False
    tool_calls_used = 0
    streamed_reply = ""
    decision: dict | None = None
    warning: dict | None = None

    try:
        if is_viz_only_message(message):
            reply = "Here is the event breakdown by variant."
            yield format_sse("token", {"content": reply})
            for frame in await _yield_block_frames(
                exp,
                message=message,
                reply=reply,
                decision=None,
                warning=None,
                tool_calls_used=0,
            ):
                yield frame
            yield format_sse(
                "done",
                {"toolCallsUsed": 0, "sduiVersion": SDUI_VERSION},
            )
            terminal_sent = True
            return

        async for evt in chat_turn_stream(exp, message, session_id):
            if evt["type"] == "token":
                streamed_reply += evt.get("content", "")
                yield format_sse("token", {"content": evt["content"]})
            elif evt["type"] == "tool_start":
                yield format_sse(
                    "tool_start",
                    {"name": evt["name"], "label": evt["label"]},
                )
            elif evt["type"] == "tool_end":
                yield format_sse(
                    "tool_end",
                    {"name": evt["name"], "ok": evt["ok"]},
                )
            elif evt["type"] == "decision":
                decision = evt.get("decision")
                yield format_sse("decision", decision)
            elif evt["type"] == "done":
                tool_calls_used = evt.get("toolCallsUsed", 0)

        for frame in await _yield_block_frames(
            exp,
            message=message,
            reply=streamed_reply,
            decision=decision,
            warning=warning,
            tool_calls_used=tool_calls_used,
        ):
            yield frame

        yield format_sse(
            "done",
            {"toolCallsUsed": tool_calls_used, "sduiVersion": SDUI_VERSION},
        )
        terminal_sent = True
    except AgentError as err:
        tool_calls_used = err.details.get("toolCallsUsed", tool_calls_used)
        if err.code in _SOFT_FAIL_CODES:
            warning = {
                "code": err.code,
                "message": user_message_for(err.code),
                "retryable": err.retryable,
            }
            yield format_sse("warning", warning)
            for frame in await _yield_block_frames(
                exp,
                message=message,
                reply=user_message_for(err.code),
                decision=None,
                warning=warning,
                tool_calls_used=tool_calls_used,
            ):
                yield frame
            yield format_sse(
                "done",
                {"toolCallsUsed": tool_calls_used, "sduiVersion": SDUI_VERSION},
            )
            terminal_sent = True
        else:
            yield format_sse(
                "error",
                {
                    "code": err.code,
                    "message": err.message,
                    "retryable": err.retryable,
                },
            )
            terminal_sent = True
    except Exception:  # noqa: BLE001
        yield format_sse(
            "error",
            {
                "code": "INTERNAL_ERROR",
                "message": user_message_for("INTERNAL_ERROR"),
                "retryable": False,
            },
        )
        terminal_sent = True
    finally:
        if not terminal_sent:
            yield format_sse(
                "done",
                {"toolCallsUsed": tool_calls_used, "sduiVersion": SDUI_VERSION},
            )
