from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from observability_service.domain.entities import LogEntry, MetricEntry


class LogRepository(ABC):
    @abstractmethod
    async def save(self, log: LogEntry) -> LogEntry:
        pass

    @abstractmethod
    async def get_by_service(
        self, service_name: str, start_time: datetime, end_time: datetime, limit: int
    ) -> list[LogEntry]:
        pass

    @abstractmethod
    async def get_by_level(
        self, level: str, start_time: datetime, end_time: datetime, limit: int
    ) -> list[LogEntry]:
        pass

    @abstractmethod
    async def get_by_trace_id(self, trace_id: str) -> list[LogEntry]:
        pass

    @abstractmethod
    async def search(self, query: str, start_time: datetime, end_time: datetime, limit: int) -> list[LogEntry]:
        pass


class MetricRepository(ABC):
    @abstractmethod
    async def save(self, metric: MetricEntry) -> MetricEntry:
        pass

    @abstractmethod
    async def get_by_service(
        self, service_name: str, metric_name: str, start_time: datetime, end_time: datetime
    ) -> list[MetricEntry]:
        pass

    @abstractmethod
    async def get_aggregated(
        self, service_name: str, metric_name: str, start_time: datetime, end_time: datetime, interval: str
    ) -> list[dict]:
        pass
