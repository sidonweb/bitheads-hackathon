from typing import Any, Optional

from pydantic import BaseModel, field_validator


class AnalyzeIn(BaseModel):
    variantAUrl: str
    variantBUrl: str

    @field_validator("variantAUrl", "variantBUrl")
    @classmethod
    def must_be_http_url(cls, value: str) -> str:
        from urllib.parse import urlparse

        value = value.strip()
        if not value:
            raise ValueError("URL must not be empty")
        parsed = urlparse(value)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("URL must be a valid http or https URL")
        return value


class AgentWarning(BaseModel):
    code: str
    message: str
    retryable: bool = False


class AgentErrorBody(BaseModel):
    code: str
    message: str
    retryable: bool = False
    details: dict = {}


class ChatMeta(BaseModel):
    toolCallsUsed: int = 0
    sduiVersion: str = "1.0"


class ChatOut(BaseModel):
    reply: str
    blocks: list[dict[str, Any]] = []
    decision: Optional[dict] = None
    warning: Optional[AgentWarning] = None
    meta: Optional[ChatMeta] = None
