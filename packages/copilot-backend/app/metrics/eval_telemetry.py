"""Live eval telemetry: log agent lifecycle events and aggregate dashboard KPIs."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text

from ..agent.statistics import decide, run_statistics
from ..db import engine

logger = logging.getLogger(__name__)

_ALLOWED_EVENT_TYPES = frozenset({
    "creation_started",
    "creation_completed",
    "config_recommended",
    "config_accepted",
    "config_rejected",
    "analysis_completed",
    "recommendation_applied",
})

_SELECT_ONLY = re.compile(r"^\s*SELECT\b", re.I | re.DOTALL)
_FORBIDDEN_SQL = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE)\b",
    re.I,
)


def log_event(
    experiment_id: str,
    event_type: str,
    payload: dict[str, Any] | None = None,
    *,
    session_id: str | None = None,
    duration_ms: int | None = None,
) -> None:
    if event_type not in _ALLOWED_EVENT_TYPES:
        logger.warning("Unknown eval event type: %s", event_type)
        return
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO agent_eval_events
                      (experiment_id, session_id, event_type, payload, duration_ms)
                    VALUES (:exp_id, :session_id, :event_type, CAST(:payload AS jsonb), :duration_ms)
                    """
                ),
                {
                    "exp_id": experiment_id,
                    "session_id": session_id,
                    "event_type": event_type,
                    "payload": json.dumps(payload or {}),
                    "duration_ms": duration_ms,
                },
            )
    except Exception as err:  # noqa: BLE001
        logger.warning("Failed to log eval event %s: %s", event_type, err)


def _load_baseline(conn, key: str, default: float) -> float:
    row = conn.execute(
        text("SELECT value FROM agent_eval_baselines WHERE key = :key"),
        {"key": key},
    ).first()
    return float(row[0]) if row else default


def _is_safe_select(sql: str) -> bool:
    stripped = sql.strip().rstrip(";").strip()
    if not stripped:
        return False
    if ";" in stripped:
        return False
    if not _SELECT_ONLY.match(stripped):
        return False
    if _FORBIDDEN_SQL.search(stripped):
        return False
    return True


def _parse_variant_counts(rows: list[dict]) -> dict[str, dict[str, float]] | None:
    """Extract {A: {success, total}, B: {success, total}} from SQL result rows."""
    by_variant: dict[str, dict[str, float]] = {}

    for row in rows:
        lower = {str(k).lower(): v for k, v in row.items()}
        variant = lower.get("variant_id") or lower.get("variant")
        if variant is None:
            continue
        variant = str(variant).upper()
        if variant not in ("A", "B"):
            continue

        exposures = lower.get("exposures") or lower.get("total") or lower.get("exposure")
        conversions = (
            lower.get("conversions")
            or lower.get("success")
            or lower.get("conversion")
            or lower.get("successes")
        )
        if exposures is not None and conversions is not None:
            by_variant[variant] = {
                "success": float(conversions),
                "total": float(exposures),
            }
            continue

        # Single-row per variant with event counts
        for key, val in lower.items():
            if key in ("variant_id", "variant"):
                continue
            if key.endswith("_total") or key == "total":
                by_variant.setdefault(variant, {})["total"] = float(val)
            elif key.endswith("_success") or key in ("success", "conversions"):
                by_variant.setdefault(variant, {})["success"] = float(val)

    if "A" in by_variant and "B" in by_variant:
        a = by_variant["A"]
        b = by_variant["B"]
        if a.get("total") and b.get("total"):
            return {
                "A": {"success": a.get("success", 0), "total": a["total"]},
                "B": {"success": b.get("success", 0), "total": b["total"]},
            }
    return None


def recompute_expert_from_sql(sql_used: str, experiment_id: str) -> dict[str, Any] | None:
    """Re-run agent aggregation SQL and derive expert decision + significance."""
    if not sql_used or not _is_safe_select(sql_used):
        return None

    sql = sql_used.strip().rstrip(";")
    try:
        with engine.begin() as conn:
            conn.execute(text("SET LOCAL statement_timeout = '5s'"))
            result = conn.execute(text(sql))
            rows = [dict(r) for r in result.mappings().all()]
    except Exception as err:  # noqa: BLE001
        logger.warning(
            "Expert recompute SQL failed experiment=%s: %s",
            experiment_id,
            err,
        )
        return None

    counts = _parse_variant_counts(rows)
    if not counts:
        return None

    stats = run_statistics(counts["A"], counts["B"])
    if stats.get("error"):
        return None

    ruled = decide(stats["p_value"], stats["uplift"], stats["sample_size"])
    return {
        "expert_decision": ruled["decision"],
        "expert_significant": stats["significant"],
        "expert_p_value": stats["p_value"],
        "expert_uplift": stats["uplift"],
        "expert_sample_size": stats["sample_size"],
    }


def build_analysis_eval_payload(
    decision: dict,
    duration_ms: int,
    *,
    experiment_id: str,
) -> dict[str, Any]:
    """Build payload for analysis_completed including expert recomputation."""
    agent_decision = decision.get("decision", "")
    agent_p_value = float(decision.get("p_value", 1.0))
    agent_significant = agent_p_value < 0.05

    payload: dict[str, Any] = {
        "agent_decision": agent_decision,
        "agent_significant": agent_significant,
        "agent_p_value": agent_p_value,
        "agent_uplift": decision.get("uplift"),
        "inferred_metric": decision.get("inferred_metric"),
        "sql_used": decision.get("sql_used", ""),
        "duration_ms": duration_ms,
    }

    expert = recompute_expert_from_sql(decision.get("sql_used", ""), experiment_id)
    if expert:
        payload.update(expert)
        payload["decision_match"] = agent_decision == expert["expert_decision"]
        payload["significance_match"] = agent_significant == expert["expert_significant"]
    else:
        # Fallback: expert from agent-submitted numbers (verifies rule application)
        sample_size = decision.get("sample_size") or {}
        ruled = decide(agent_p_value, float(decision.get("uplift", 0)), sample_size)
        payload["expert_decision"] = ruled["decision"]
        payload["expert_significant"] = agent_significant
        payload["decision_match"] = agent_decision == ruled["decision"]
        payload["significance_match"] = True
        payload["expert_source"] = "submitted_stats"

    return payload


def _parse_payload(raw: Any) -> dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return {}


def aggregate_dashboard() -> dict[str, Any]:
    with engine.begin() as conn:
        creation_baseline = _load_baseline(conn, "manual_creation_minutes", 45.0)
        analysis_baseline = _load_baseline(conn, "manual_analysis_minutes", 120.0)

        events = conn.execute(
            text(
                """
                SELECT id, experiment_id, session_id, event_type, payload, duration_ms, created_at
                  FROM agent_eval_events
                 ORDER BY created_at DESC
                 LIMIT 500
                """
            )
        ).mappings().all()

        all_events = [dict(e) for e in events]

    # --- creation time reduction ---
    creation_durations = [
        e["duration_ms"]
        for e in all_events
        if e["event_type"] == "creation_completed" and e.get("duration_ms")
    ]
    avg_creation_ms = (
        sum(creation_durations) / len(creation_durations) if creation_durations else 0
    )
    avg_creation_min = avg_creation_ms / 60_000
    creation_reduction = (
        ((creation_baseline - avg_creation_min) / creation_baseline * 100)
        if creation_durations and creation_baseline > 0
        else 0.0
    )

    # --- config acceptance ---
    config_recommended = sum(1 for e in all_events if e["event_type"] == "config_recommended")
    config_accepted = sum(1 for e in all_events if e["event_type"] == "config_accepted")
    config_rate = config_accepted / config_recommended if config_recommended else 0.0

    # --- analysis accuracy ---
    analysis_events = [
        e for e in all_events if e["event_type"] == "analysis_completed"
    ]
    decision_correct = 0
    significance_correct = 0
    analysis_durations: list[int] = []

    for evt in analysis_events:
        payload = _parse_payload(evt.get("payload"))
        if evt.get("duration_ms"):
            analysis_durations.append(evt["duration_ms"])
        elif payload.get("duration_ms"):
            analysis_durations.append(int(payload["duration_ms"]))

        if payload.get("decision_match"):
            decision_correct += 1
        if payload.get("significance_match"):
            significance_correct += 1

    analysis_total = len(analysis_events)
    decision_rate = decision_correct / analysis_total if analysis_total else 0.0
    significance_rate = significance_correct / analysis_total if analysis_total else 0.0

    avg_analysis_ms = (
        sum(analysis_durations) / len(analysis_durations) if analysis_durations else 0
    )
    avg_analysis_sec = avg_analysis_ms / 1000
    avg_analysis_min = avg_analysis_ms / 60_000
    analysis_reduction = (
        ((analysis_baseline - avg_analysis_min) / analysis_baseline * 100)
        if analysis_durations and analysis_baseline > 0
        else 0.0
    )

    # --- adoption rate ---
    eligible = 0
    for evt in analysis_events:
        payload = _parse_payload(evt.get("payload"))
        if payload.get("agent_decision") in ("Scale", "Rollback"):
            eligible += 1

    applied = sum(1 for e in all_events if e["event_type"] == "recommendation_applied")
    adoption_rate = applied / eligible if eligible else 0.0

    # --- recent events feed ---
    recent = []
    for evt in all_events[:20]:
        payload = _parse_payload(evt.get("payload"))
        recent.append({
            "id": evt["id"],
            "experimentId": evt["experiment_id"],
            "eventType": evt["event_type"],
            "createdAt": evt["created_at"].isoformat() if evt.get("created_at") else None,
            "summary": _event_summary(evt["event_type"], payload),
        })

    # --- 7-day trends ---
    now = datetime.now(timezone.utc)
    daily_buckets: dict[str, dict[str, int]] = {}
    for i in range(7):
        day = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        daily_buckets[day] = {
            "analyses": 0,
            "configAccepted": 0,
            "applied": 0,
        }

    for evt in all_events:
        created = evt.get("created_at")
        if not created:
            continue
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        day_key = created.strftime("%Y-%m-%d")
        if day_key not in daily_buckets:
            continue
        et = evt["event_type"]
        if et == "analysis_completed":
            daily_buckets[day_key]["analyses"] += 1
        elif et == "config_accepted":
            daily_buckets[day_key]["configAccepted"] += 1
        elif et == "recommendation_applied":
            daily_buckets[day_key]["applied"] += 1

    daily_trend = [
        {"date": day, **daily_buckets[day]}
        for day in sorted(daily_buckets.keys())
    ]

    return {
        "creationTimeReduction": {
            "baselineMinutes": creation_baseline,
            "avgAiMinutes": round(avg_creation_min, 2),
            "reductionPct": round(max(0.0, creation_reduction), 1),
            "sampleSize": len(creation_durations),
        },
        "configAcceptanceRate": {
            "accepted": config_accepted,
            "recommended": config_recommended,
            "rate": round(config_rate, 3),
        },
        "recommendationAccuracy": {
            "correct": decision_correct,
            "total": analysis_total,
            "rate": round(decision_rate, 3),
        },
        "significanceAccuracy": {
            "correct": significance_correct,
            "total": analysis_total,
            "rate": round(significance_rate, 3),
        },
        "analysisTimeReduction": {
            "baselineMinutes": analysis_baseline,
            "avgAiSeconds": round(avg_analysis_sec, 1),
            "reductionPct": round(max(0.0, analysis_reduction), 1),
            "sampleSize": len(analysis_durations),
        },
        "adoptionRate": {
            "applied": applied,
            "eligible": eligible,
            "rate": round(adoption_rate, 3),
        },
        "recentEvents": recent,
        "trends": {"daily": daily_trend},
    }


def _event_summary(event_type: str, payload: dict) -> str:
    if event_type == "analysis_completed":
        agent = payload.get("agent_decision", "?")
        expert = payload.get("expert_decision", "?")
        match = "✓" if payload.get("decision_match") else "✗"
        return f"Analysis → {agent} (expert: {expert}) {match}"
    if event_type == "config_recommended":
        metric = payload.get("recommendedMetric", "?")
        return f"Recommended metric: {metric}"
    if event_type == "config_accepted":
        return f"Accepted metric: {payload.get('primaryMetric', '?')}"
    if event_type == "config_rejected":
        return "Config recommendation dismissed"
    if event_type == "recommendation_applied":
        return f"Applied {payload.get('decision', '?')} → {payload.get('trafficSplit', '?')}% B"
    if event_type == "creation_completed":
        ms = payload.get("durationMs") or payload.get("duration_ms")
        return f"Experiment setup in {round(ms / 1000, 1) if ms else '?'}s"
    if event_type == "creation_started":
        return "Started AI-assisted experiment setup"
    return event_type.replace("_", " ")
