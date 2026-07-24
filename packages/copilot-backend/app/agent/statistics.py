import math

# Deterministic two-proportion z-test. The LLM never does this math — it calls
# the run_statistics tool which wraps this. Inputs: successes (conversions) and
# totals (exposures) per variant.

MIN_SAMPLE_PER_VARIANT = 300  # sufficiency threshold for the "Continue" branch


def _two_sided_p(z: float) -> float:
    # Standard normal CDF via math.erf; two-sided tail.
    cdf = 0.5 * (1 + math.erf(abs(z) / math.sqrt(2)))
    return 2 * (1 - cdf)


def run_statistics(control: dict, treatment: dict) -> dict:
    a_success, a_total = float(control["success"]), float(control["total"])
    b_success, b_total = float(treatment["success"]), float(treatment["total"])

    if a_total <= 0 or b_total <= 0:
        return {"error": "both variants need total > 0"}

    p_a = a_success / a_total
    p_b = b_success / b_total
    p_pool = (a_success + b_success) / (a_total + b_total)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / a_total + 1 / b_total))

    z = 0.0 if se == 0 else (p_b - p_a) / se
    p_value = _two_sided_p(z)
    uplift = 0.0 if p_a == 0 else (p_b - p_a) / p_a

    return {
        "control_rate": p_a,
        "treatment_rate": p_b,
        "absolute_diff": p_b - p_a,
        "uplift": uplift,  # relative, e.g. 0.14 = +14%
        "z_score": z,
        "p_value": p_value,
        "confidence": 1 - p_value,
        "significant": p_value < 0.05,
        "sample_size": {"A": int(a_total), "B": int(b_total)},
    }


def decide(p_value: float, uplift: float, sample_size: dict) -> dict:
    n_a = sample_size.get("A", 0)
    n_b = sample_size.get("B", 0)
    enough = n_a >= MIN_SAMPLE_PER_VARIANT and n_b >= MIN_SAMPLE_PER_VARIANT
    significant = p_value < 0.05

    if not enough:
        return {"decision": "Continue", "rationale": "insufficient sample size"}
    if significant and uplift > 0:
        return {"decision": "Scale", "rationale": "B significantly better"}
    if significant and uplift < 0:
        return {"decision": "Rollback", "rationale": "B significantly worse"}
    if not significant and abs(uplift) > 0:
        return {"decision": "Continue", "rationale": "trending but not yet significant"}
    return {"decision": "Stop", "rationale": "no meaningful difference detected"}
