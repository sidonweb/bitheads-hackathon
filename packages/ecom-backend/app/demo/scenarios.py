"""Demo scenario profiles — variation presets for storefront UI; one experiment row in DB."""

import os

EXPERIMENT_ID = os.getenv("EXPERIMENT_ID", "exp_1")
DEFAULT_VARIATION = "checkout-cta"

# Full funnel vocabulary — always seeded/simulated so any variation can be analyzed.
EXPOSURE = "page_view"
FULL_FUNNEL = ["add_to_cart", "checkout_started", "checkout_completed"]

VARIATION_IDS = [
    "checkout-cta",
    "plp-social-proof",
    "pdp-sticky-cta",
    "cart-shipping-nudge",
]

VARIATION_PRESETS = {
    "checkout-cta": {
        "name": "Checkout CTA Redesign",
        "hypothesis": "Variant B's redesigned checkout CTA increases checkout conversion vs Variant A.",
        "variant_a_name": "Original CTA",
        "variant_b_name": "Redesigned CTA",
        "surface": "checkout",
        "primary_metric": "checkout_completed",
        "default_rates": {"A": 0.158, "B": 0.18},
    },
    "plp-social-proof": {
        "name": "PLP Social Proof",
        "hypothesis": "Showing star ratings and review counts on product cards increases add-to-cart rate.",
        "variant_a_name": "No Ratings",
        "variant_b_name": "Star Ratings",
        "surface": "listing",
        "primary_metric": "add_to_cart",
        "default_rates": {"A": 0.12, "B": 0.145},
    },
    "pdp-sticky-cta": {
        "name": "PDP Sticky CTA",
        "hypothesis": "A sticky bottom add-to-cart bar on product detail increases add-to-cart rate.",
        "variant_a_name": "Inline CTA",
        "variant_b_name": "Sticky CTA Bar",
        "surface": "detail",
        "primary_metric": "add_to_cart",
        "default_rates": {"A": 0.14, "B": 0.165},
    },
    "cart-shipping-nudge": {
        "name": "Cart Free-Shipping Nudge",
        "hypothesis": "A free-shipping progress bar nudges more users from cart into checkout.",
        "variant_a_name": "Standard Cart",
        "variant_b_name": "Shipping Nudge",
        "surface": "cart",
        "primary_metric": "checkout_started",
        "default_rates": {"A": 0.22, "B": 0.195},
    },
}


def variation_urls(ecom_web_url: str, variation_id: str) -> tuple[str, str]:
    if variation_id not in VARIATION_PRESETS:
        raise ValueError(f"unknown variation: {variation_id}")
    base = ecom_web_url.rstrip("/")
    q = f"variation={variation_id}"
    if variation_id == "checkout-cta":
        return (
            f"{base}/?{q}&variant=A&screen=checkout",
            f"{base}/?{q}&variant=B&screen=checkout",
        )
    if variation_id == "plp-social-proof":
        return (
            f"{base}/?{q}&variant=A",
            f"{base}/?{q}&variant=B",
        )
    if variation_id == "pdp-sticky-cta":
        return (
            f"{base}/?{q}&variant=A&screen=detail&product=p1",
            f"{base}/?{q}&variant=B&screen=detail&product=p1",
        )
    if variation_id == "cart-shipping-nudge":
        return (
            f"{base}/?{q}&variant=A&screen=cart&product=p8",
            f"{base}/?{q}&variant=B&screen=cart&product=p8",
        )
    raise ValueError(f"unknown variation: {variation_id}")


def get_variation_preset(variation_id: str) -> dict:
    if variation_id not in VARIATION_PRESETS:
        raise ValueError(f"unknown variation: {variation_id}")
    return VARIATION_PRESETS[variation_id]


# Legacy exports (checkout-cta defaults).
METRIC = VARIATION_PRESETS[DEFAULT_VARIATION]["primary_metric"]
FUNNEL_ON_CONVERT = FULL_FUNNEL


def _scale_rates() -> dict[str, float]:
    return dict(VARIATION_PRESETS[DEFAULT_VARIATION]["default_rates"])


def _rollback_rates() -> dict[str, float]:
    return {"A": 0.18, "B": 0.158}


SCENARIOS = {
    "scale": {
        "label": "scale · B wins",
        "rates": _scale_rates(),
        "users_per_variant": 5000,
        "expected_verdict": "Scale",
    },
    "rollback": {
        "label": "rollback · B loses",
        "rates": _rollback_rates(),
        "users_per_variant": 5000,
        "expected_verdict": "Rollback",
    },
    "continue": {
        "label": "continue · underpowered",
        "rates": _scale_rates(),
        "users_per_variant": 100,
        "expected_verdict": "Continue",
    },
    "stop": {
        "label": "stop · no winner",
        "rates": {"A": 0.16, "B": 0.161},
        "users_per_variant": 5000,
        "expected_verdict": "Stop",
    },
    "empty": {
        "label": "empty · just launched",
        "rates": {"A": 0.0, "B": 0.0},
        "users_per_variant": 0,
        "expected_verdict": None,
    },
    "live": {
        "label": "live · manual traffic",
        "rates": {"A": 0.0, "B": 0.0},
        "users_per_variant": 0,
        "expected_verdict": None,
    },
}

SCENARIO_IDS = list(SCENARIOS.keys())


def variant_urls(ecom_web_url: str, variation_id: str = DEFAULT_VARIATION) -> tuple[str, str]:
    return variation_urls(ecom_web_url, variation_id)
