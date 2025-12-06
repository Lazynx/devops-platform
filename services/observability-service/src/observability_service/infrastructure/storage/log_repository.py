from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from observability_service.application.interfaces import LogRepository
from observability_service.domain.entities import LogEntry, LogLevel, ServiceName


class SqlAlchemyLogRepository(LogRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, log: LogEntry) -> LogEntry:
        self._session.add(log)
        await self._session.flush()
        await self._session.refresh(log)
        return log

    async def get_by_service(
        self, service_name: str, start_time: datetime, end_time: datetime, limit: int = 1000
    ) -> list[LogEntry]:
        result = await self._session.execute(
            select(LogEntry)
            .where(
                LogEntry.service_name == ServiceName(service_name),
                LogEntry.timestamp >= start_time,
                LogEntry.timestamp <= end_time,
            )
            .order_by(LogEntry.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_level(
        self, level: str, start_time: datetime, end_time: datetime, limit: int = 1000
    ) -> list[LogEntry]:
        result = await self._session.execute(
            select(LogEntry)
            .where(
                LogEntry.level == LogLevel(level),
                LogEntry.timestamp >= start_time,
                LogEntry.timestamp <= end_time,
            )
            .order_by(LogEntry.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_trace_id(self, trace_id: str) -> list[LogEntry]:
        result = await self._session.execute(
            select(LogEntry).where(LogEntry.trace_id == trace_id).order_by(LogEntry.timestamp.asc())
        )
        return list(result.scalars().all())

    async def search(
        self, query: str, start_time: datetime, end_time: datetime, limit: int = 1000
    ) -> list[LogEntry]:
        search_pattern = f'%{query}%'
        result = await self._session.execute(
            select(LogEntry)
            .where(
                or_(
                    LogEntry.message.ilike(search_pattern),
                    LogEntry.logger_name.ilike(search_pattern),
                    LogEntry.exception.ilike(search_pattern),
                ),
                LogEntry.timestamp >= start_time,
                LogEntry.timestamp <= end_time,
            )
            .order_by(LogEntry.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
