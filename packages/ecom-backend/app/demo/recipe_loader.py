"""Load journey recipe from shared volume (written by copilot discovery)."""

import json
import os
from pathlib import Path

_PKG_ROOT = Path(__file__).resolve().parents[2]
RECIPE_DIR = Path(os.getenv("JOURNEY_RECIPE_DIR", str(_PKG_ROOT / "data")))

DEFAULT = {
    "exposureEvent": "page_view",
    "conversionEvent": "checkout_completed",
    "funnelOnConvert": ["add_to_cart", "checkout_started", "checkout_completed"],
}


def load_recipe(experiment_id: str) -> dict:
    path = RECIPE_DIR / f"journey_recipe_{experiment_id}.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {**DEFAULT, "experimentId": experiment_id}
