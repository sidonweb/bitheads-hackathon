"""Pydantic models and error helpers for FR-01/02/03 lifecycle endpoints."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def api_error(
    code: str,
    message: str,
    retryable: bool = False,
    details: dict | None = None,
) -> dict:
    return {
        "code": code,
        "message": message,
        "retryable": retryable,
        "details": details or {},
    }


class LifecycleError(Exception):
    """Structured API error raised from services and routes."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        retryable: bool = False,
        details: dict | None = None,
    ):
        self.status_code = status_code
        self.error = api_error(code, message, retryable, details)
        super().__init__(message)


# --- FR-01 -------------------------------------------------------------------


class GenerateHypothesisIn(BaseModel):
    businessGoal: str
    context: str = ""

    @field_validator("businessGoal")
    @classmethod
    def validate_business_goal(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Business goal is required.")
        if len(value) > 2000:
            raise ValueError("Business goal must be at most 2000 characters.")
        return stripped

    @field_validator("context")
    @classmethod
    def validate_context(cls, value: str) -> str:
        if len(value) > 2000:
            raise ValueError("Context must be at most 2000 characters.")
        return value


class GenerateHypothesisOut(BaseModel):
    hypothesis: str
    suggestedName: str
    suggestedVariantAName: str = "Control"
    suggestedVariantBName: str = "Treatment"
    confidence: Literal["low", "medium", "high"] = "medium"


# --- FR-02 -------------------------------------------------------------------


class RecommendConfigIn(BaseModel):
    hypothesis: str = ""
    variantAUrl: Optional[str] = None
    variantBUrl: Optional[str] = None

    @field_validator("hypothesis")
    @classmethod
    def validate_hypothesis(cls, value: str) -> str:
        if len(value) > 4000:
            raise ValueError("Hypothesis must be at most 4000 characters.")
        return value

    @field_validator("variantAUrl", "variantBUrl")
    @classmethod
    def validate_url(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value == "":
            return value
        if not value.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return value


class PrimaryMetricRecommendation(BaseModel):
    eventName: str
    rationale: str
    alternatives: list[str] = Field(default_factory=list)


class FeatureFlagRecommendation(BaseModel):
    summary: str
    suggestedTrafficSplit: int = 50


class AudienceRecommendation(BaseModel):
    suggestion: str
    note: str = "Audience targeting not enforced in v1.5; stored for documentation."


class RecommendConfigOut(BaseModel):
    primaryMetric: PrimaryMetricRecommendation
    featureFlag: FeatureFlagRecommendation
    audience: AudienceRecommendation
    availableEvents: list[str]
    warning: Optional[str] = None


class RecommendConfigLLMOut(BaseModel):
    """Structured LLM output for config recommendation."""

    primaryMetric: PrimaryMetricRecommendation
    featureFlag: FeatureFlagRecommendation
    audience: AudienceRecommendation


# --- FR-03 -------------------------------------------------------------------


class CheckStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class PreflightCheck(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str
    name: str
    status: CheckStatus
    message: str


class PreflightResult(BaseModel):
    ready: bool
    score: str
    checks: list[PreflightCheck]
    evaluatedAt: datetime
