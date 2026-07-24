from typing import Optional
from pydantic import BaseModel


class ExperimentIn(BaseModel):
    id: str
    name: str
    hypothesis: str = ""
    primaryMetric: Optional[str] = None  # nullable: agent infers it
    variantAName: str = "Control"
    variantBName: str = "Treatment"
    variantAUrl: Optional[str] = None
    variantBUrl: Optional[str] = None
    trafficSplit: int = 50


class ExperimentPatch(BaseModel):
    trafficSplit: Optional[int] = None
    status: Optional[str] = None
    variantAUrl: Optional[str] = None
    variantBUrl: Optional[str] = None


class ChatIn(BaseModel):
    message: str
    sessionId: Optional[str] = None  # isolates each conversation's history


class SampleSize(BaseModel):
    A: int
    B: int


class Decision(BaseModel):
    decision: str
    confidence: float
    p_value: float
    uplift: float
    sample_size: SampleSize
    reasoning: str
    sql_used: str
    control: str = "A"
    treatment: str = "B"
    rule_rationale: str = ""
