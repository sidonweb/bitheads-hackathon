from typing import Any, Optional

from pydantic import BaseModel, Field


class EvalEventIn(BaseModel):
    experimentId: str
    eventType: str
    sessionId: Optional[str] = None
    durationMs: Optional[int] = None
    payload: dict[str, Any] = Field(default_factory=dict)


class TimeReductionMetric(BaseModel):
    baselineMinutes: float
    avgAiMinutes: float = 0
    avgAiSeconds: float = 0
    reductionPct: float = 0
    sampleSize: int = 0


class RateMetric(BaseModel):
    accepted: int = 0
    recommended: int = 0
    correct: int = 0
    total: int = 0
    applied: int = 0
    eligible: int = 0
    rate: float = 0


class RecentEvalEvent(BaseModel):
    id: int
    experimentId: str
    eventType: str
    createdAt: Optional[str] = None
    summary: str = ""


class DailyTrendPoint(BaseModel):
    date: str
    analyses: int = 0
    configAccepted: int = 0
    applied: int = 0


class EvalDashboardOut(BaseModel):
    creationTimeReduction: TimeReductionMetric
    configAcceptanceRate: RateMetric
    recommendationAccuracy: RateMetric
    significanceAccuracy: RateMetric
    analysisTimeReduction: TimeReductionMetric
    adoptionRate: RateMetric
    recentEvents: list[RecentEvalEvent]
    trends: dict[str, list[DailyTrendPoint]]
