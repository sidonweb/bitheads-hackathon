# Deterministic variant assignment: the same userId always lands in the same
# bucket for a given experiment, so a user's variant is stable across reloads.
# bucket in [0, 99]; if bucket < trafficSplit -> Variant B, else A.
# FNV-1a 32-bit, matching the previous JS implementation's contract.


def _hash_to_bucket(experiment_id: str, user_id: str) -> int:
    s = f"{experiment_id}:{user_id}"
    h = 2166136261
    for ch in s:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return h % 100


def assign_variant(experiment_id: str, user_id: str, traffic_split: int) -> str:
    return "B" if _hash_to_bucket(experiment_id, user_id) < traffic_split else "A"
