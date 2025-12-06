import logging
from datetime import datetime

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException, Query, status

from observability_service.application.interfaces import LogRepository, MetricRepository
from observability_service.presentation.api.schemas import (
    AggregatedMetricResponse,
    LogEntryResponse,
    LogQueryRequest,
    MetricEntryResponse,
    MetricQueryRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/v1/observability', tags=['Observability'])


@router.post('/logs/query', response_model=list[LogEntryResponse])
@inject
async def query_logs(request: LogQueryRequest, log_repo: FromDishka[LogRepository]) -> list[LogEntryResponse]:
    try:
        if request.trace_id:
            logs = await log_repo.get_by_trace_id(request.trace_id)
        elif request.search_query:
            logs = await log_repo.search(
                request.search_query, request.start_time, request.end_time, request.limit
            )
        elif request.level:
            logs = await log_repo.get_by_level(request.level, request.start_time, request.end_time, request.limit)
        elif request.service_name:
            logs = await log_repo.get_by_service(
                request.service_name, request.start_time, request.end_time, request.limit
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Must provide at least one filter: service_name, level, trace_id, or search_query',
            )

        return [
            LogEntryResponse(
                id=log.id,
                timestamp=log.timestamp,
                service_name=log.service_name.value,
                level=log.level.value,
                message=log.message,
                logger_name=log.logger_name,
                trace_id=log.trace_id,
                user_id=str(log.user_id) if log.user_id else None,
                request_id=log.request_id,
                context=log.context,
                exception=log.exception,
            )
            for log in logs
        ]

    except Exception as e:
        logger.error(f'Failed to query logs: {e}', exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get('/logs/service/{service_name}', response_model=list[LogEntryResponse])
@inject
async def get_logs_by_service(
    service_name: str,
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    limit: int = Query(1000, le=10000),
    log_repo: FromDishka[LogRepository] = None,
) -> list[LogEntryResponse]:
    try:
        logs = await log_repo.get_by_service(service_name, start_time, end_time, limit)

        return [
            LogEntryResponse(
                id=log.id,
                timestamp=log.timestamp,
                service_name=log.service_name.value,
                level=log.level.value,
                message=log.message,
                logger_name=log.logger_name,
                trace_id=log.trace_id,
                user_id=str(log.user_id) if log.user_id else None,
                request_id=log.request_id,
                context=log.context,
                exception=log.exception,
            )
            for log in logs
        ]

    except Exception as e:
        logger.error(f'Failed to get logs: {e}', exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post('/metrics/query', response_model=list[AggregatedMetricResponse])
@inject
async def query_metrics(
    request: MetricQueryRequest, metric_repo: FromDishka[MetricRepository]
) -> list[AggregatedMetricResponse]:
    try:
        metrics = await metric_repo.get_aggregated(
            request.service_name, request.metric_name, request.start_time, request.end_time, request.interval
        )

        return [AggregatedMetricResponse(**metric) for metric in metrics]

    except Exception as e:
        logger.error(f'Failed to query metrics: {e}', exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get('/metrics/service/{service_name}/{metric_name}', response_model=list[MetricEntryResponse])
@inject
async def get_metrics_by_service(
    service_name: str,
    metric_name: str,
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    metric_repo: FromDishka[MetricRepository] = None,
) -> list[MetricEntryResponse]:
    try:
        metrics = await metric_repo.get_by_service(service_name, metric_name, start_time, end_time)

        return [
            MetricEntryResponse(
                id=metric.id,
                timestamp=metric.timestamp,
                service_name=metric.service_name.value,
                metric_name=metric.metric_name,
                metric_type=metric.metric_type.value,
                value=metric.value,
                labels=metric.labels,
            )
            for metric in metrics
        ]

    except Exception as e:
        logger.error(f'Failed to get metrics: {e}', exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
