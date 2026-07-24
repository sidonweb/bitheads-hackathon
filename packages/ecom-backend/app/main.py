from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import events, flag, demo

app = FastAPI(title="Ecom Backend — telemetry + flags")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}


# ecom-backend owns event ingestion and the variant flag.
app.include_router(events.router)
app.include_router(flag.router)
app.include_router(demo.router)
