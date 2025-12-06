from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from observability_service.application.interfaces import MetricRepository
from observability_service.domain.entities import MetricEntry, ServiceName


class SqlAlchemyMetricRepository(MetricRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, metric: MetricEntry) -> MetricEntry:
        self._session.add(metric)
        await self._session.flush()
        await self._session.refresh(metric)
        return metric

    async def get_by_service(
        self, service_name: str, metric_name: str, start_time: datetime, end_time: datetime
    ) -> list[MetricEntry]:
        result = await self._session.execute(
            select(MetricEntry)
            .where(
                MetricEntry.service_name == ServiceName(service_name),
                MetricEntry.metric_name == metric_name,
                MetricEntry.timestamp >= start_time,
                MetricEntry.timestamp <= end_time,
            )
            .order_by(MetricEntry.timestamp.asc())
        )
        return list(result.scalars().all())

    async def get_aggregated(
        self, service_name: str, metric_name: str, start_time: datetime, end_time: datetime, interval: str
    ) -> list[dict]:
        interval_expr = func.date_trunc(interval, MetricEntry.timestamp)

        result = await self._session.execute(
            select(
                interval_expr.label('timestamp'),
                func.avg(MetricEntry.value).label('avg'),
                func.min(MetricEntry.value).label('min'),
                func.max(MetricEntry.value).label('max'),
                func.count(MetricEntry.id).label('count'),
            )
            .where(
                MetricEntry.service_name == ServiceName(service_name),
                MetricEntry.metric_name == metric_name,
                MetricEntry.timestamp >= start_time,
                MetricEntry.timestamp <= end_time,
            )
            .group_by(interval_expr)
            .order_by(interval_expr.asc())
        )

        return [
            {
                'timestamp': row.timestamp,
                'avg': float(row.avg) if row.avg else 0.0,
                'min': float(row.min) if row.min else 0.0,
                'max': float(row.max) if row.max else 0.0,
                'count': row.count,
            }
            for row in result.all()
        ]
