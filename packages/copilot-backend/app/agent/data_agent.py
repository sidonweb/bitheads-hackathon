"""Read-only data sub-agent exposed to the main analyst via ask_data_analyst."""

from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from ..config import (
    LLM_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    XAI_API_KEY,
    XAI_MODEL,
)
from .sql_tools import describe_table, list_tables, run_readonly_query

_SQL_FENCE = re.compile(r"```(?:sql)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def _build_llm():
    if LLM_PROVIDER == "xai":
        from langchain_xai import ChatXAI

        return ChatXAI(model=XAI_MODEL, api_key=XAI_API_KEY, temperature=0)

    from langchain_openai import ChatOpenAI

    kwargs = {"model": OPENAI_MODEL, "api_key": OPENAI_API_KEY, "temperature": 0}
    if OPENAI_BASE_URL:
        kwargs["base_url"] = OPENAI_BASE_URL
    return ChatOpenAI(**kwargs)


def _bootstrap_schema() -> tuple[str, list[str]]:
    tables_payload = json.loads(list_tables.invoke({"schema": "public"}))
    table_names = tables_payload.get("tables", [])
    lines = [f"Available tables: {', '.join(table_names)}"]
    for name in table_names:
        desc = json.loads(describe_table.invoke({"table_name": name}))
        cols = [c["name"] for c in desc.get("columns", [])]
        lines.append(f"{name} columns: {', '.join(cols)}")
    return "\n".join(lines), table_names


def _extract_sql(text: str) -> str:
    match = _SQL_FENCE.search(text)
    if match:
        return match.group(1).strip()
    return text.strip().strip("`")


async def _generate_sql(llm, schema_context: str, question: str, prior_error: str = "") -> str:
    system = (
        "You write exactly ONE PostgreSQL SELECT query. Output ONLY the SQL — no prose, no markdown.\n"
        "Rules: SELECT only; scope by experiment_id when provided; use FILTER aggregates for event counts;\n"
        "never INSERT/UPDATE/DELETE; prefer GROUP BY variant_id for A/B comparisons.\n"
        "Use only column names from the schema (event_name, not event_type)."
    )
    user = f"Schema:\n{schema_context}\n\nQuestion: {question}"
    if prior_error:
        user += (
            f"\n\nPrevious query failed: {prior_error}\n"
            "SELF-CHECK before retry:\n"
            "1. Am I using a column that does not exist? Re-read the schema.\n"
            "2. Is experiment_id scoped correctly?\n"
            "3. Are aggregate/FILTER expressions valid PostgreSQL?\n"
            "Write ONE corrected SELECT."
        )
    response = await llm.ainvoke([SystemMessage(content=system), HumanMessage(content=user)])
    content = response.content if isinstance(response.content, str) else str(response.content)
    return _extract_sql(content)


def _summarize_rows(question: str, payload: dict) -> str:
    rows = payload.get("rows", [])
    columns = payload.get("columns", [])
    if not rows:
        return "No rows returned for this query."
    preview = rows[:5]
    return (
        f"Answer for: {question}\n"
        f"Columns: {', '.join(columns)}\n"
        f"Rows ({payload.get('rowCount', len(rows))} total, showing up to 5): {preview}"
    )


async def run_data_agent(question: str) -> dict:
    """Discover schema, generate one SELECT, execute, return structured answer."""
    schema_context, table_names = _bootstrap_schema()
    llm = _build_llm()
    sql_used: list[str] = []
    last_error = ""

    for _attempt in range(2):
        sql_text = await _generate_sql(llm, schema_context, question, last_error)
        result = json.loads(run_readonly_query.invoke({"sql_text": sql_text}))
        sql_used.append(result.get("sql", sql_text))
        if result.get("error"):
            last_error = result["error"]
            continue
        return {
            "answer": _summarize_rows(question, result),
            "sql_used": sql_used,
            "tables_used": table_names,
            "error": None,
        }

    return {
        "answer": "",
        "sql_used": sql_used,
        "tables_used": table_names,
        "error": last_error or "Could not run a valid SELECT query.",
    }


def make_ask_data_analyst_tool():
    @tool
    async def ask_data_analyst(question: str) -> str:
        """Ask the read-only data analyst to discover schema and run SQL.
        Include experiment id and what aggregates you need. Returns JSON with
        answer, sql_used, tables_used."""
        result = await run_data_agent(question)
        return json.dumps(result)

    return ask_data_analyst
