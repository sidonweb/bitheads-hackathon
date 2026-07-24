"""Persist and load journey recipes (shared via /app/data volume in compose)."""

import json
import os
from pathlib import Path

_PKG_ROOT = Path(__file__).resolve().parents[2]
RECIPE_DIR = Path(os.getenv("JOURNEY_RECIPE_DIR", str(_PKG_ROOT / "data")))

DEFAULT_RECIPE = {
    "exposureEvent": "page_view",
    "conversionEvent": "checkout_completed",
    "funnelEvents": ["page_view", "add_to_cart", "checkout_started", "checkout_completed"],
    "funnelOnConvert": ["add_to_cart", "checkout_started", "checkout_completed"],
    "discoveredVia": "default",
}


def recipe_path(experiment_id: str) -> Path:
    RECIPE_DIR.mkdir(parents=True, exist_ok=True)
    return RECIPE_DIR / f"journey_recipe_{experiment_id}.json"


def save_recipe(experiment_id: str, recipe: dict) -> dict:
    payload = {**recipe, "experimentId": experiment_id}
    recipe_path(experiment_id).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def load_recipe(experiment_id: str) -> dict | None:
    path = recipe_path(experiment_id)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def get_recipe_or_default(experiment_id: str) -> dict:
    loaded = load_recipe(experiment_id)
    if loaded:
        return loaded
    return {**DEFAULT_RECIPE, "experimentId": experiment_id}
