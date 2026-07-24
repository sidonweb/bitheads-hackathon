"""Agent guardrails: tool budgets, safe invocation, structured errors."""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

from langchain_core.tools import BaseTool
from langgraph.errors import GraphRecursionError

from ..config import AGENT_LLM_TIMEOUT_SEC, AGENT_RECURSION_LIMIT


class AgentError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        retryable: bool = False,
        details: dict | None = None,
    ):
        self.code = code
        self.message = message
        self.retryable = retryable
        self.details = details or {}
        super().__init__(message)


_MESSAGES = {
    "AGENT_TOOL_LIMIT": (
        "This analysis needed too many steps. Try asking a simpler question, "
        "or use Analyze once."
    ),
    "AGENT_RECURSION_LIMIT": (
        "I hit my thinking limit for this turn. Please try again or narrow your question."
    ),
    "AGENT_NO_DECISION": (
        "I couldn't produce a final recommendation. Check pre-flight status and "
        "try Analyze again."
    ),
    "LLM_UNAVAILABLE": (
        "Copilot is temporarily unavailable. Live metrics in the drawer are still updating."
    ),
    "INTERNAL_ERROR": (
        "Something unexpected happened. Your experiment data is safe — please retry."
    ),
    "VALIDATION_ERROR": "Request validation failed.",
    "UPSTREAM_ERROR": "An upstream service failed. Please retry shortly.",
}


def user_message_for(code: str) -> str:
    return _MESSAGES.get(code, _MESSAGES["INTERNAL_ERROR"])


def http_status_for(code: str) -> int:
    return {
        "NOT_FOUND": 404,
        "VALIDATION_ERROR": 422,
        "AGENT_TOOL_LIMIT": 429,
        "AGENT_RECURSION_LIMIT": 429,
        "AGENT_NO_DECISION": 502,
        "LLM_UNAVAILABLE": 503,
        "UPSTREAM_ERROR": 502,
        "INTERNAL_ERROR": 500,
    }.get(code, 500)


class ToolCallBudget:
    def __init__(self, limit: int):
        self.limit = limit
        self.count = 0

    def increment(self) -> None:
        self.count += 1
        if self.count > self.limit:
            raise AgentError(
                code="AGENT_TOOL_LIMIT",
                message=user_message_for("AGENT_TOOL_LIMIT"),
                retryable=True,
                details={"toolCallsUsed": self.count - 1},
            )


class ToolFailureTracker:
    """Track per-tool failures in one turn to cap blind retries."""

    def __init__(self, max_retries_per_tool: int = 1):
        self.max_retries_per_tool = max_retries_per_tool
        self._counts: dict[str, int] = {}

    def record_failure(self, tool_name: str) -> int:
        self._counts[tool_name] = self._counts.get(tool_name, 0) + 1
        return self._counts[tool_name]

    def should_block_retry(self, tool_name: str) -> bool:
        return self._counts.get(tool_name, 0) > self.max_retries_per_tool


def parse_tool_error(tool_name: str, output: Any) -> tuple[bool, str]:
    """Return (is_error, error_detail) for a tool result."""
    text = output if isinstance(output, str) else str(output)
    lowered = text.lower().strip()

    if tool_name == "ask_data_analyst":
        try:
            payload = json.loads(text)
            if isinstance(payload, dict):
                err = payload.get("error")
                if err:
                    return True, str(err)
                if not payload.get("answer") and payload.get("sql_used"):
                    return True, "Data analyst returned SQL but no answer rows."
        except json.JSONDecodeError:
            pass

    if lowered.startswith("(browser inspection failed") or lowered.startswith("missing a url"):
        return True, text

    if '"error"' in lowered:
        try:
            payload = json.loads(text)
            if isinstance(payload, dict) and payload.get("error"):
                return True, str(payload["error"])
        except json.JSONDecodeError:
            if "error" in lowered[:120]:
                return True, text[:300]

    return False, ""


def tool_error_recovery_block(
    tool_name: str,
    *,
    experiment_id: str | None,
    error_detail: str,
    failure_count: int,
    block_retry: bool,
) -> str:
    """Structured self-check the agent must run before retrying a failed tool."""
    exp = experiment_id or "(this experiment)"
    verify_inputs = [
        f"experiment_id is exactly '{exp}' in every data question",
        "both variant URLs came from the PM's chat (not invented or from config)",
        "data questions use column event_name (NOT event_type) and variant_id IN ('A','B')",
        "run_statistics uses integer {{success, total}} from ask_data_analyst — never guessed",
        "inspect_variant_pages receives two full http(s) URLs unchanged from chat",
    ]
    if tool_name == "ask_data_analyst":
        verify_inputs.append(
            "the question is plain English describing the aggregate needed — no SQL pasted"
        )

    lines = [
        "=== TOOL ERROR — SELF-CHECK LOOP (mandatory before retry) ===",
        f"Tool: {tool_name} | failure #{failure_count} this turn",
        f"Error: {error_detail[:500]}",
        "",
        'Step 1 — Ask: "Am I doing something wrong?"',
        "   Yes. A tool failed because inputs or approach were wrong. Do not ignore this.",
        "",
        "Step 2 — Verify ALL inputs you passed:",
    ]
    for item in verify_inputs:
        lines.append(f"   • {item}")

    if block_retry:
        lines.extend(
            [
                "",
                "Step 3 — STOP: this tool already failed twice. Do NOT call it again this turn.",
                "Tell the PM briefly what blocked you and what they can verify.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "Step 3 — Fix the root cause, then retry this tool ONCE with corrected inputs.",
                "Do not repeat the same mistake or call other tools until you have verified inputs.",
            ]
        )
    return "\n".join(lines)


def enrich_tool_error_output(
    tool_name: str,
    output: Any,
    *,
    experiment_id: str | None,
    tracker: ToolFailureTracker,
) -> Any:
    """Append a recovery checklist when a tool returns an error."""
    is_error, detail = parse_tool_error(tool_name, output)
    if not is_error:
        return output

    failure_count = tracker.record_failure(tool_name)
    block = tool_error_recovery_block(
        tool_name,
        experiment_id=experiment_id,
        error_detail=detail,
        failure_count=failure_count,
        block_retry=tracker.should_block_retry(tool_name),
    )

    text = output if isinstance(output, str) else str(output)
    if tool_name == "ask_data_analyst":
        try:
            payload = json.loads(text)
            if isinstance(payload, dict):
                payload["self_check"] = {
                    "question": "Am I doing something wrong?",
                    "verify_inputs": [
                        f"experiment_id={experiment_id}",
                        "event_name column (not event_type)",
                        "URLs from PM chat",
                    ],
                    "block_retry": tracker.should_block_retry(tool_name),
                    "recovery": block,
                }
                return json.dumps(payload)
        except json.JSONDecodeError:
            pass

    return f"{text}\n\n{block}"


def _wrap_one_tool(
    tool: BaseTool,
    budget: ToolCallBudget,
    *,
    experiment_id: str | None,
    failure_tracker: ToolFailureTracker,
) -> BaseTool:
    if getattr(tool, "coroutine", None):
        original = tool.coroutine

        async def wrapped(*args: Any, **kwargs: Any) -> Any:
            budget.increment()
            result = await original(*args, **kwargs)
            return enrich_tool_error_output(
                tool.name,
                result,
                experiment_id=experiment_id,
                tracker=failure_tracker,
            )

        return tool.copy(update={"coroutine": wrapped})

    original = tool.func

    def wrapped(*args: Any, **kwargs: Any) -> Any:
        budget.increment()
        result = original(*args, **kwargs)
        return enrich_tool_error_output(
            tool.name,
            result,
            experiment_id=experiment_id,
            tracker=failure_tracker,
        )

    return tool.copy(update={"func": wrapped})


def wrap_tools(
    tools: list[BaseTool],
    budget: ToolCallBudget,
    *,
    experiment_id: str | None = None,
    failure_tracker: ToolFailureTracker | None = None,
) -> list[BaseTool]:
    tracker = failure_tracker or ToolFailureTracker()
    return [
        _wrap_one_tool(
            t,
            budget,
            experiment_id=experiment_id,
            failure_tracker=tracker,
        )
        for t in tools
    ]


async def run_agent_safe(
    agent,
    input_messages: dict,
    config: dict,
    budget: ToolCallBudget,
    capture: dict,
    *,
    expect_decision: bool = False,
    experiment_id: str | None = None,
) -> dict:
    """Invoke the LangGraph agent with guardrails. Raises AgentError on failure."""
    merged_config = {
        **config,
        "recursion_limit": AGENT_RECURSION_LIMIT,
    }

    try:
        result = await asyncio.wait_for(
            agent.ainvoke(input_messages, config=merged_config),
            timeout=AGENT_LLM_TIMEOUT_SEC,
        )
    except AgentError:
        raise
    except asyncio.TimeoutError as err:
        raise AgentError(
            code="LLM_UNAVAILABLE",
            message=user_message_for("LLM_UNAVAILABLE"),
            retryable=True,
        ) from err
    except GraphRecursionError as err:
        raise AgentError(
            code="AGENT_RECURSION_LIMIT",
            message=user_message_for("AGENT_RECURSION_LIMIT"),
            retryable=True,
            details={"toolCallsUsed": budget.count},
        ) from err
    except Exception as err:  # noqa: BLE001
        correlation_id = str(uuid.uuid4())
        print(
            f"ERROR experiment_id={experiment_id} correlation_id={correlation_id} "
            f"exception={err}"
        )
        raise AgentError(
            code="INTERNAL_ERROR",
            message=user_message_for("INTERNAL_ERROR"),
            retryable=False,
            details={"correlationId": correlation_id},
        ) from err

    reply = result["messages"][-1].content
    decision = capture.get("decision")

    if expect_decision and decision is None:
        raise AgentError(
            code="AGENT_NO_DECISION",
            message=user_message_for("AGENT_NO_DECISION"),
            retryable=True,
            details={"toolCallsUsed": budget.count},
        )

    verdict = decision.get("decision") if decision else None
    print(
        f"INFO experiment_id={experiment_id} tool_calls={budget.count} "
        f"verdict={verdict or 'none'}"
    )

    return {
        "reply": reply,
        "decision": decision,
        "tool_calls_used": budget.count,
        "error": None,
    }
