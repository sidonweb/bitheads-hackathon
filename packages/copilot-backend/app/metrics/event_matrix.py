"""Dynamic variant × event_name pivot for dashboard tables."""

from sqlalchemy import text
from sqlalchemy.engine import Connection

EXPOSURE_EVENT = "page_view"
CONVERSION_EVENT = "checkout_completed"
VARIANTS = ("A", "B")


def _order_event_names(
    names: set[str],
    exposure_event: str,
    conversion_event: str | None,
) -> list[str]:
    middle = sorted(n for n in names if n not in {exposure_event, conversion_event})
    ordered: list[str] = []
    if exposure_event in names:
        ordered.append(exposure_event)
    ordered.extend(middle)
    if conversion_event and conversion_event in names and conversion_event not in ordered:
        ordered.append(conversion_event)
    for n in sorted(names):
        if n not in ordered:
            ordered.append(n)
    return ordered


def build_event_matrix(
    conn: Connection,
    experiment_id: str,
    primary_metric: str | None = None,
) -> dict:
    exposure_event = EXPOSURE_EVENT
    conversion_event = primary_metric or CONVERSION_EVENT

    raw = conn.execute(
        text(
            """
            SELECT variant_id, event_name, COUNT(*)::int AS cnt
              FROM universal_events
             WHERE experiment_id = :id
             GROUP BY variant_id, event_name
            """
        ),
        {"id": experiment_id},
    ).mappings().all()

    counts: dict[str, dict[str, int]] = {v: {} for v in VARIANTS}
    event_names: set[str] = set()
    for row in raw:
        vid = row["variant_id"]
        ename = row["event_name"]
        event_names.add(ename)
        if vid in counts:
            counts[vid][ename] = row["cnt"]

    ordered_events = _order_event_names(event_names, exposure_event, conversion_event)

    rows = []
    for variant_id in VARIANTS:
        vc = counts.get(variant_id, {})
        exposures = vc.get(exposure_event, 0)
        conv = vc.get(conversion_event, 0) if conversion_event else 0
        rate = (conv / exposures) if exposures and conversion_event else None
        rows.append(
            {
                "variant_id": variant_id,
                "counts": {e: vc.get(e, 0) for e in ordered_events},
                "conversionRate": rate,
            }
        )

    return {
        "exposureEvent": exposure_event,
        "conversionEvent": conversion_event,
        "eventNames": ordered_events,
        "rows": rows,
    }
