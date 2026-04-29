"""Telemetri / analitik veri transfer objeleri."""

from datetime import datetime

from pydantic import BaseModel, Field


class RequestLog(BaseModel):
    """Her API isteginin log kaydi. analytics koleksiyonuna yazilir."""

    user_id: str | None = None
    method: str
    endpoint: str
    status_code: int
    process_time_ms: float
    ip_address: str = ""
    user_agent: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
