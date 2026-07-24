from typing import Optional
from pydantic import BaseModel


class EventIn(BaseModel):
    userId: str
    experimentId: str
    variantId: str
    eventName: str
    metricValue: float = 0
    timestamp: Optional[str] = None


class BulkEventsIn(BaseModel):
    events: list[EventIn]
