"""Read-only SQL tools for the data sub-agent (SELECT-only, agent_readonly role)."""

from __future__ import annotations

import json
import re

import psycopg
from langchain_core.tools import tool
from psycopg import sql

from ..config import AGENT_DATABASE_URL

_BLOCKED = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT)\b",
    re.IGNORECASE,
)
_LIMIT_RE = re.compile(r"\bLIMIT\b", re.IGNORECASE)


def _connect():
    return psycopg.connect(AGENT_DATABASE_URL, autocommit=True)


def _list_tables_raw(schema: str = "public") -> list[str]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT table_name
              FROM information_schema.tables
             WHERE table_schema = %s
               AND table_type = 'BASE TABLE'
             ORDER BY table_name
            """,
            (schema,),
        ).fetchall()
    return [row[0] for row in rows]


def _validate_select(sql_text: str) -> str | None:
    stripped = sql_text.strip()
    if not stripped.upper().startswith("SELECT"):
        return "Query must start with SELECT"
    if _BLOCKED.search(stripped):
        return "Query contains a blocked keyword"
    return None


def _append_limit(sql_text: str) -> str:
    if _LIMIT_RE.search(sql_text):
        return sql_text
    return f"{sql_text.rstrip().rstrip(';')} LIMIT 500"


@tool
def list_tables(schema: str = "public") -> str:
    """List base tables visible to the read-only agent role in the given schema."""
    try:
        tables = _list_tables_raw(schema)
        return json.dumps({"schema": schema, "tables": tables})
    except Exception as err:  # noqa: BLE001
        return json.dumps({"schema": schema, "tables": [], "error": str(err)})


@tool
def describe_table(table_name: str, schema: str = "public") -> str:
    """Describe columns, row estimate, and up to two sample rows for a table."""
    allowed = _list_tables_raw(schema)
    if table_name not in allowed:
        return json.dumps({"error": f"Unknown table: {table_name}"})

    try:
        with _connect() as conn:
            columns = conn.execute(
                """
                SELECT column_name, data_type, is_nullable
                  FROM information_schema.columns
                 WHERE table_schema = %s
                   AND table_name = %s
                 ORDER BY ordinal_position
                """,
                (schema, table_name),
            ).fetchall()
            row_count_row = conn.execute(
                "SELECT reltuples::bigint FROM pg_class WHERE relname = %s",
                (table_name,),
            ).fetchone()
            sample_rows = conn.execute(
                sql.SQL("SELECT * FROM {}.{} LIMIT 2").format(
                    sql.Identifier(schema),
                    sql.Identifier(table_name),
                )
            ).fetchall()
            col_names = [c[0] for c in columns]
            samples = [dict(zip(col_names, row)) for row in sample_rows]

        return json.dumps(
            {
                "table": table_name,
                "columns": [
                    {"name": name, "type": dtype, "nullable": nullable == "YES"}
                    for name, dtype, nullable in columns
                ],
                "row_count_estimate": int(row_count_row[0]) if row_count_row else 0,
                "sample_rows": samples,
            }
        )
    except Exception as err:  # noqa: BLE001
        return json.dumps({"table": table_name, "error": str(err)})


@tool
def run_readonly_query(sql_text: str) -> str:
    """Execute a read-only SELECT query. Non-SELECT statements are rejected."""
    validation_error = _validate_select(sql_text)
    if validation_error:
        return json.dumps({"error": validation_error, "sql": sql_text})

    final_sql = _append_limit(sql_text)
    try:
        with _connect() as conn:
            cur = conn.execute(final_sql)
            if cur.description is None:
                return json.dumps(
                    {"columns": [], "rows": [], "rowCount": 0, "sql": final_sql}
                )
            columns = [desc.name for desc in cur.description]
            rows = [list(row) for row in cur.fetchall()]
        return json.dumps(
            {
                "columns": columns,
                "rows": rows,
                "rowCount": len(rows),
                "sql": final_sql,
            }
        )
    except Exception as err:  # noqa: BLE001
        return json.dumps({"error": str(err), "sql": final_sql})
