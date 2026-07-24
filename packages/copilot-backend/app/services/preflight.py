"""Deterministic pre-launch validation checks for FR-03."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit

import httpx
from sqlalchemy import text

from ..agent.graph import _browser_url
from ..config import PLAYWRIGHT_LOCALHOST_ALIAS
from ..schemas_lifecycle import CheckStatus, PreflightCheck, PreflightResult

logger = logging.getLogger(__name__)

CHECK_ORDER = ["C1b", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]
CACHE_TTL_SECONDS = 60

_cache: dict[str, tuple[PreflightResult, float]] = {}


def docker_reachable_url(url: str) -> str:
    """Rewrite localhost hostnames for container-to-container fetch."""
    rewritten = _browser_url(url)
    return rewritten or url


async def check_url_reachable(
    url: str,
    *,
    timeout: float = 5.0,
) -> tuple[CheckStatus, int | None, float | None, str]:
    """Return status, HTTP code, latency_ms, and a human-readable message."""
    fetch_url = docker_reachable_url(url)
    started = time.monotonic()
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(fetch_url, timeout=timeout)
        latency_ms = (time.monotonic() - started) * 1000
        code = response.status_code
        if 200 <= code < 400:
            status = CheckStatus.WARN if latency_ms > 3000 else CheckStatus.PASS
            message = f"HTTP {code} in {int(latency_ms)}ms"
            if status == CheckStatus.WARN:
                message += " (slow response)"
            return status, code, latency_ms, message
        message = f"Unreachable: {url} — HTTP {code}"
        return CheckStatus.FAIL, code, latency_ms, message
    except httpx.TimeoutException:
        return (
            CheckStatus.FAIL,
            None,
            None,
            f"Unreachable: {url} — request timed out after {int(timeout)}s",
        )
    except httpx.RequestError as err:
        return (
            CheckStatus.FAIL,
            None,
            None,
            f"Unreachable: {url} — {err.__class__.__name__.replace('Error', '').lower()}",
        )


def resolve_variant_urls(
    experiment: dict[str, Any],
    query_a: str | None,
    query_b: str | None,
) -> tuple[str | None, str | None, PreflightCheck]:
    url_a = query_a or experiment.get("variant_a_url")
    url_b = query_b or experiment.get("variant_b_url")

    if url_a and url_b:
        check = PreflightCheck(
            id="C1b",
            name="Variant URLs provided",
            status=CheckStatus.PASS,
            message="Both variant URLs configured.",
        )
    elif url_a or url_b:
        check = PreflightCheck(
            id="C1b",
            name="Variant URLs provided",
            status=CheckStatus.WARN,
            message="Only one variant URL configured.",
        )
    else:
        check = PreflightCheck(
            id="C1b",
            name="Variant URLs provided",
            status=CheckStatus.WARN,
            message="Paste variant URLs in chat or save them on the experiment before launch.",
        )
    return url_a, url_b, check


async def check_c1_variant_a(url: str | None) -> PreflightCheck:
    if not url:
        return PreflightCheck(
            id="C1",
            name="Variant A URL reachable",
            status=CheckStatus.WARN,
            message="URL not provided",
        )
    status, _code, _latency, message = await check_url_reachable(url)
    return PreflightCheck(
        id="C1",
        name="Variant A URL reachable",
        status=status,
        message=message,
    )


async def check_c2_variant_b(url: str | None) -> PreflightCheck:
    if not url:
        return PreflightCheck(
            id="C2",
            name="Variant B URL reachable",
            status=CheckStatus.WARN,
            message="URL not provided",
        )
    status, _code, _latency, message = await check_url_reachable(url)
    return PreflightCheck(
        id="C2",
        name="Variant B URL reachable",
        status=status,
        message=message,
    )


def check_c3_events(conn, experiment_id: str) -> PreflightCheck:
    count = conn.execute(
        text("SELECT COUNT(*) FROM universal_events WHERE experiment_id = :id"),
        {"id": experiment_id},
    ).scalar_one()
    if count == 0:
        return PreflightCheck(
            id="C3",
            name="Events exist for experiment",
            status=CheckStatus.FAIL,
            message=f"No events for experiment {experiment_id}",
        )
    if count < 100:
        return PreflightCheck(
            id="C3",
            name="Events exist for experiment",
            status=CheckStatus.WARN,
            message=f"{count:,} events recorded (under 100 — collect more data)",
        )
    return PreflightCheck(
        id="C3",
        name="Events exist for experiment",
        status=CheckStatus.PASS,
        message=f"{count:,} events recorded",
    )


def _exposure_counts(conn, experiment_id: str) -> dict[str, int]:
    rows = conn.execute(
        text(
            """
            SELECT variant_id, COUNT(*) AS n
              FROM universal_events
             WHERE experiment_id = :id
               AND event_name = 'page_view'
             GROUP BY variant_id
            """
        ),
        {"id": experiment_id},
    ).mappings().all()
    return {str(row["variant_id"]): int(row["n"]) for row in rows}


def check_c4_exposures(exposures: dict[str, int]) -> PreflightCheck:
    exp_a = exposures.get("A", 0)
    exp_b = exposures.get("B", 0)
    if exp_a >= 1 and exp_b >= 1:
        return PreflightCheck(
            id="C4",
            name="Exposures (page_view) per variant",
            status=CheckStatus.PASS,
            message=f"Variant A: {exp_a:,} exposures; Variant B: {exp_b:,} exposures",
        )
    if exp_a == 0 and exp_b == 0:
        return PreflightCheck(
            id="C4",
            name="Exposures (page_view) per variant",
            status=CheckStatus.FAIL,
            message="No page_view exposures recorded for either variant",
        )
    missing = "A" if exp_a == 0 else "B"
    present = "B" if missing == "A" else "A"
    count = exposures.get(present, 0)
    return PreflightCheck(
        id="C4",
        name="Exposures (page_view) per variant",
        status=CheckStatus.WARN,
        message=f"Variant {missing} has 0 exposures; Variant {present} has {count:,}",
    )


def check_c5_traffic_split(experiment: dict[str, Any]) -> PreflightCheck:
    split = experiment.get("traffic_split")
    if split is None or not isinstance(split, int) or split < 0 or split > 100:
        return PreflightCheck(
            id="C5",
            name="Traffic split",
            status=CheckStatus.FAIL,
            message=f"Invalid traffic split: {split!r}",
        )
    if split == 0 or split == 100:
        return PreflightCheck(
            id="C5",
            name="Traffic split",
            status=CheckStatus.WARN,
            message=f"Traffic split is {split} — one variant receives no traffic",
        )
    return PreflightCheck(
        id="C5",
        name="Traffic split",
        status=CheckStatus.PASS,
        message=f"Traffic split is {split}% to variant B",
    )


def check_c6_hypothesis(experiment: dict[str, Any]) -> PreflightCheck:
    hypothesis = (experiment.get("hypothesis") or "").strip()
    if hypothesis:
        return PreflightCheck(
            id="C6",
            name="Hypothesis configured",
            status=CheckStatus.PASS,
            message="Hypothesis configured",
        )
    return PreflightCheck(
        id="C6",
        name="Hypothesis configured",
        status=CheckStatus.FAIL,
        message="Hypothesis is empty — use Generate hypothesis or enter manually",
    )


def check_c7_sample_size(exposures: dict[str, int]) -> PreflightCheck:
    exp_a = exposures.get("A", 0)
    exp_b = exposures.get("B", 0)
    minimum = min(exp_a, exp_b)
    if minimum >= 300:
        return PreflightCheck(
            id="C7",
            name="Sample size guidance",
            status=CheckStatus.PASS,
            message=f"Minimum variant exposures: {minimum:,} (A={exp_a:,}, B={exp_b:,})",
        )
    if minimum >= 50:
        return PreflightCheck(
            id="C7",
            name="Sample size guidance",
            status=CheckStatus.WARN,
            message=f"Minimum variant exposures: {minimum:,} — aim for 300+ (A={exp_a:,}, B={exp_b:,})",
        )
    return PreflightCheck(
        id="C7",
        name="Sample size guidance",
        status=CheckStatus.FAIL,
        message=f"Insufficient exposures: minimum {minimum:,} (A={exp_a:,}, B={exp_b:,}) — need at least 50",
    )


def check_c8_overlap(conn) -> PreflightCheck:
    experiment_count = conn.execute(
        text("SELECT COUNT(DISTINCT experiment_id) FROM universal_events"),
    ).scalar_one()
    if experiment_count <= 1:
        return PreflightCheck(
            id="C8",
            name="Experiment overlap",
            status=CheckStatus.PASS,
            message="Single experiment in system",
        )

    overlap_rows = conn.execute(
        text(
            """
            SELECT user_id, COUNT(DISTINCT experiment_id) AS n
              FROM universal_events
             GROUP BY user_id
            HAVING COUNT(DISTINCT experiment_id) > 1
             LIMIT 5
            """
        ),
    ).mappings().all()

    if overlap_rows:
        user_ids = ", ".join(str(row["user_id"]) for row in overlap_rows)
        count = len(overlap_rows)
        suffix = "" if count < 5 else "+"
        return PreflightCheck(
            id="C8",
            name="Experiment overlap",
            status=CheckStatus.FAIL,
            message=f"{count}{suffix} users appear in multiple experiments: {user_ids}",
        )

    return PreflightCheck(
        id="C8",
        name="Experiment overlap",
        status=CheckStatus.PASS,
        message="No user overlap detected across experiments",
    )


def _cache_key(experiment_id: str, url_a: str | None, url_b: str | None) -> str:
    raw = f"{url_a or ''}|{url_b or ''}"
    url_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"preflight:{experiment_id}:{url_hash}"


def _score(checks: list[PreflightCheck]) -> str:
    passed = sum(1 for check in checks if check.status == CheckStatus.PASS)
    return f"{passed}/{len(checks)}"


async def run_preflight(
    *,
    experiment_id: str,
    experiment: dict[str, Any],
    variant_a_url: str | None,
    variant_b_url: str | None,
    conn,
) -> PreflightResult:
    """Run all preflight checks in stable order with optional 60s caching."""
    url_a, url_b, c1b = resolve_variant_urls(experiment, variant_a_url, variant_b_url)
    cache_key = _cache_key(experiment_id, url_a, url_b)
    now = time.monotonic()
    cached = _cache.get(cache_key)
    if cached and (now - cached[1]) < CACHE_TTL_SECONDS:
        logger.info("Preflight cache hit experiment_id=%s", experiment_id)
        return cached[0]

    c1, c2 = await asyncio.gather(
        check_c1_variant_a(url_a),
        check_c2_variant_b(url_b),
    )
    c3 = check_c3_events(conn, experiment_id)
    exposures = _exposure_counts(conn, experiment_id)
    c4 = check_c4_exposures(exposures)
    c5 = check_c5_traffic_split(experiment)
    c6 = check_c6_hypothesis(experiment)
    c7 = check_c7_sample_size(exposures)
    c8 = check_c8_overlap(conn)

    checks = [c1b, c1, c2, c3, c4, c5, c6, c7, c8]
    ready = not any(check.status == CheckStatus.FAIL for check in checks)
    result = PreflightResult(
        ready=ready,
        score=_score(checks),
        checks=checks,
        evaluatedAt=datetime.now(timezone.utc),
    )
    _cache[cache_key] = (result, now)
    logger.info(
        "Preflight complete experiment_id=%s ready=%s score=%s alias=%s",
        experiment_id,
        ready,
        result.score,
        PLAYWRIGHT_LOCALHOST_ALIAS or "(none)",
    )
    return result
