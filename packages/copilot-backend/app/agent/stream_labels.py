"""Human-readable labels for agent tool events in streaming chat."""

TOOL_LABELS: dict[str, str] = {
    # Main analyst tools
    "ask_data_analyst": "Querying experiment data",
    "run_statistics": "Running statistical test",
    "submit_decision": "Applying decision rules",
    "inspect_variant_pages": "Inspecting variant page",
    # Data sub-agent SQL tools
    "list_tables": "Listing available tables",
    "describe_table": "Inspecting data schema",
    "run_readonly_query": "Querying experiment data",
    # Legacy LangChain SQL toolkit names
    "sql_db_query": "Querying experiment data",
    "sql_db_schema": "Inspecting data schema",
    "sql_db_list_tables": "Listing available tables",
}


def label_for_tool(name: str) -> str:
    """Return a PM-friendly label for a tool name."""
    if name in TOOL_LABELS:
        return TOOL_LABELS[name]
    if name.startswith("browser_"):
        return "Inspecting variant page"
    return "Running analysis step"
