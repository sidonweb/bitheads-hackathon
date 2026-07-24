import os
from dotenv import load_dotenv

load_dotenv()

# copilot-backend owns experiment CRUD (copilot_role: SELECT/INSERT/UPDATE on experiments).
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://copilot_role:copilot_pw@localhost:5432/copilot"
)

# Read-only connection used exclusively by the agent's SQL toolkit.
# Backed by a SELECT-only role — the guardrail at the DB layer.
AGENT_DATABASE_URL = os.getenv(
    "AGENT_DATABASE_URL", "postgresql://agent_readonly:agent_pw@localhost:5432/copilot"
)

# LLM provider selection: "openai" (default) or "xai".
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()

# OpenAI (also works for OpenAI-compatible gateways like OpenRouter via OPENAI_BASE_URL).
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")  # empty = OpenAI default endpoint

# Grok (xAI). Set XAI_API_KEY in the environment.
XAI_API_KEY = os.getenv("XAI_API_KEY", "")
XAI_MODEL = os.getenv("XAI_MODEL", "grok-3-mini")

# Playwright MCP server (browser tools the agent uses to inspect variant URLs).
PLAYWRIGHT_MCP_URL = os.getenv("PLAYWRIGHT_MCP_URL", "http://localhost:8931/mcp")
# Hostname the containerized browser should use when an experiment URL points at
# localhost. Empty string disables rewriting.
PLAYWRIGHT_LOCALHOST_ALIAS = os.getenv("PLAYWRIGHT_LOCALHOST_ALIAS", "host.docker.internal")
# Toggle: if false, the agent skips browser inspection and infers from chat only.
USE_PLAYWRIGHT = os.getenv("USE_PLAYWRIGHT", "true").lower() == "true"

PORT = int(os.getenv("PORT", "3001"))
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
