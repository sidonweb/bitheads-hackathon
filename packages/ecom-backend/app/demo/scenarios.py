"""Demo scenario profiles — same ecom storefront, different metrics stories."""

import os

EXPERIMENT_ID = os.getenv("EXPERIMENT_ID", "exp_1")
METRIC = "checkout_completed"
EXPOSURE = "page_view"

# Funnel events fired on conversion (matches packages/ecom/src/App.jsx).
FUNNEL_ON_CONVERT = ["add_to_cart", "checkout_started", "checkout_completed"]

SCENARIOS = {
    "scale": {
        "label": "scale · B wins",
        "name": "Checkout CTA Redesign",
        "hypothesis": "Variant B's redesigned checkout CTA increases checkout conversion vs Variant A.",
        "variant_a_name": "Original CTA",
        "variant_b_name": "Redesigned CTA",
        "rates": {"A": 0.158, "B": 0.18},
        "users_per_variant": 5000,
        "traffic_split": 50,
        "expected_verdict": "Scale",
    },
    "rollback": {
        "label": "rollback · B loses",
        "name": "Checkout CTA Redesign",
        "hypothesis": "Variant B's redesigned checkout CTA increases checkout conversion vs Variant A.",
        "variant_a_name": "Original CTA",
        "variant_b_name": "Redesigned CTA",
        "rates": {"A": 0.18, "B": 0.158},
        "users_per_variant": 5000,
        "traffic_split": 50,
        "expected_verdict": "Rollback",
    },
    "continue": {
        "label": "continue · underpowered",
        "name": "Checkout CTA Redesign",
        "hypothesis": "Variant B's redesigned checkout CTA increases checkout conversion vs Variant A.",
        "variant_a_name": "Original CTA",
        "variant_b_name": "Redesigned CTA",
        "rates": {"A": 0.158, "B": 0.18},
        "users_per_variant": 100,
        "traffic_split": 50,
        "expected_verdict": "Continue",
    },
    "stop": {
        "label": "stop · no winner",
        "name": "Checkout CTA Redesign",
        "hypothesis": "Variant B's redesigned checkout CTA increases checkout conversion vs Variant A.",
        "variant_a_name": "Original CTA",
        "variant_b_name": "Redesigned CTA",
        "rates": {"A": 0.16, "B": 0.161},
        "users_per_variant": 5000,
        "traffic_split": 50,
        "expected_verdict": "Stop",
    },
    "empty": {
        "label": "empty · just launched",
        "name": "Checkout CTA Redesign",
        "hypothesis": "Variant B's redesigned checkout CTA increases checkout conversion vs Variant A.",
        "variant_a_name": "Original CTA",
        "variant_b_name": "Redesigned CTA",
        "rates": {"A": 0.0, "B": 0.0},
        "users_per_variant": 0,
        "traffic_split": 50,
        "expected_verdict": None,
    },
    "live": {
        "label": "live · manual traffic",
        "name": "Checkout CTA Redesign",
        "hypothesis": "Variant B's redesigned checkout CTA increases checkout conversion vs Variant A.",
        "variant_a_name": "Original CTA",
        "variant_b_name": "Redesigned CTA",
        "rates": {"A": 0.0, "B": 0.0},
        "users_per_variant": 0,
        "traffic_split": 50,
        "expected_verdict": None,
    },
}

SCENARIO_IDS = list(SCENARIOS.keys())


def variant_urls(ecom_web_url: str) -> tuple[str, str]:
    base = ecom_web_url.rstrip("/")
    return f"{base}/?variant=A", f"{base}/?variant=B"
