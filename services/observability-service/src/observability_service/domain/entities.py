from datetime import UTC, datetime
from enum import Enum as PyEnum
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Enum as SqlEnum, Index, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class LogLevel(str, PyEnum):
    DEBUG = 'debug'
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'


class ServiceName(str, PyEnum):
    AUTH_SERVICE = 'auth-service'
    PROJECT_SERVICE = 'project-service'
    DEPLOYMENT_SERVICE = 'deployment-service'
    SECRETS_SERVICE = 'secrets-service'
    CI_SERVICE = 'ci-service'
    OBSERVABILITY_SERVICE = 'observability-service'


class LogEntry(Base):
    __tablename__ = 'log_entries'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    service_name: Mapped[ServiceName] = mapped_column(SqlEnum(ServiceName), nullable=False, index=True)
    level: Mapped[LogLevel] = mapped_column(SqlEnum(LogLevel), nullable=False, index=True)

    message: Mapped[str] = mapped_column(Text, nullable=False)
    logger_name: Mapped[str] = mapped_column(String(255), nullable=True)

    trace_id: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    span_id: Mapped[str] = mapped_column(String(255), nullable=True)
    user_id: Mapped[UUID] = mapped_column(String(255), nullable=True, index=True)
    request_id: Mapped[str] = mapped_column(String(255), nullable=True, index=True)

    context: Mapped[dict] = mapped_column(JSON, nullable=True)
    exception: Mapped[str] = mapped_column(Text, nullable=True)
    stack_trace: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index('idx_service_timestamp', 'service_name', 'timestamp'),
        Index('idx_level_timestamp', 'level', 'timestamp'),
        Index('idx_trace_id', 'trace_id'),
    )


class MetricType(str, PyEnum):
    COUNTER = 'counter'
    GAUGE = 'gauge'
    HISTOGRAM = 'histogram'
    SUMMARY = 'summary'


class MetricEntry(Base):
    __tablename__ = 'metric_entries'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    service_name: Mapped[ServiceName] = mapped_column(SqlEnum(ServiceName), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    metric_type: Mapped[MetricType] = mapped_column(SqlEnum(MetricType), nullable=False)

    value: Mapped[float] = mapped_column(nullable=False)
    labels: Mapped[dict] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index('idx_service_metric_timestamp', 'service_name', 'metric_name', 'timestamp'),
        Index('idx_metric_timestamp', 'metric_name', 'timestamp'),
    )
