from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LogEntryResponse(BaseModel):
    id: UUID
    timestamp: datetime
    service_name: str
    level: str
    message: str
    logger_name: str | None
    trace_id: str | None
    user_id: str | None
    request_id: str | None
    context: dict | None
    exception: str | None


class MetricEntryResponse(BaseModel):
    id: UUID
    timestamp: datetime
    service_name: str
    metric_name: str
    metric_type: str
    value: float
    labels: dict | None


class AggregatedMetricResponse(BaseModel):
    timestamp: datetime
    avg: float
    min: float
    max: float
    count: int


class LogQueryRequest(BaseModel):
    service_name: str | None = None
    level: str | None = None
    trace_id: str | None = None
    search_query: str | None = None
    start_time: datetime
    end_time: datetime
    limit: int = Field(default=1000, le=10000)


class MetricQueryRequest(BaseModel):
    service_name: str
    metric_name: str
    start_time: datetime
    end_time: datetime
    interval: str = Field(default='hour', pattern='^(minute|hour|day)$')
