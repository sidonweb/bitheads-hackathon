from dotenv import load_dotenv

load_dotenv()  # before LangChain imports so LangSmith env vars are visible locally

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import experiments, analyze, chat, demo, lifecycle, evals
from .agent.graph import _load_playwright_tools


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Warm the Playwright MCP tools once, inside the running loop.
    await _load_playwright_tools()
    yield


app = FastAPI(title="Experiment Copilot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}


# copilot-backend owns experiments, the agent, chat, and analysis.
app.include_router(experiments.router)
app.include_router(analyze.router)
app.include_router(chat.router)
app.include_router(demo.router)
app.include_router(lifecycle.router)
app.include_router(evals.router)
