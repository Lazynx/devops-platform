import logging
from datetime import datetime
from uuid import UUID

from faststream.kafka import KafkaBroker
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from observability_service.domain.entities import LogEntry, LogLevel, MetricEntry, MetricType, ServiceName
from observability_service.infrastructure.storage.log_repository import SqlAlchemyLogRepository
from observability_service.infrastructure.storage.metric_repository import SqlAlchemyMetricRepository

logger = logging.getLogger(__name__)

broker = KafkaBroker()

_session_factory: async_sessionmaker[AsyncSession] | None = None


def set_session_factory(factory: async_sessionmaker[AsyncSession]) -> None:
    global _session_factory
    _session_factory = factory


@broker.subscriber('application.log')
async def handle_application_log(event: dict) -> None:
    if not _session_factory:
        logger.error('Session factory not initialized')
        return

    try:
        async with _session_factory() as session:
            async with session.begin():
                log_repo = SqlAlchemyLogRepository(session)

                log_entry = LogEntry(
                    timestamp=datetime.fromisoformat(event['timestamp']),
                    service_name=ServiceName(event['service_name']),
                    level=LogLevel(event['level'].lower()),
                    message=event['message'],
                    logger_name=event.get('logger_name'),
                    trace_id=event.get('trace_id'),
                    span_id=event.get('span_id'),
                    user_id=UUID(event['user_id']) if event.get('user_id') else None,
                    request_id=event.get('request_id'),
                    context=event.get('context'),
                    exception=event.get('exception'),
                    stack_trace=event.get('stack_trace'),
                )

                await log_repo.save(log_entry)
                logger.debug(f'Saved log entry from {event["service_name"]}: {event["message"][:50]}')

    except Exception as e:
        logger.error(f'Failed to process log event: {e}', exc_info=True)


@broker.subscriber('application.metric')
async def handle_application_metric(event: dict) -> None:
    if not _session_factory:
        logger.error('Session factory not initialized')
        return

    try:
        async with _session_factory() as session:
            async with session.begin():
                metric_repo = SqlAlchemyMetricRepository(session)

                metric_entry = MetricEntry(
                    timestamp=datetime.fromisoformat(event['timestamp']),
                    service_name=ServiceName(event['service_name']),
                    metric_name=event['metric_name'],
                    metric_type=MetricType(event['metric_type']),
                    value=float(event['value']),
                    labels=event.get('labels'),
                )

                await metric_repo.save(metric_entry)
                logger.debug(
                    f'Saved metric from {event["service_name"]}: {event["metric_name"]} = {event["value"]}'
                )

    except Exception as e:
        logger.error(f'Failed to process metric event: {e}', exc_info=True)


@broker.subscriber('deployment.created')
@broker.subscriber('deployment.started')
@broker.subscriber('deployment.completed')
@broker.subscriber('deployment.failed')
@broker.subscriber('secret.created')
@broker.subscriber('secret.updated')
@broker.subscriber('secret.deleted')
@broker.subscriber('project.created')
async def handle_system_event(event: dict, topic: str) -> None:
    if not _session_factory:
        return

    try:
        async with _session_factory() as session:
            async with session.begin():
                log_repo = SqlAlchemyLogRepository(session)

                service_name = topic.split('.')[0]
                event_type = topic.split('.')[1]

                log_entry = LogEntry(
                    timestamp=datetime.now(),
                    service_name=ServiceName(f'{service_name}-service'),
                    level=LogLevel.INFO,
                    message=f'{service_name.capitalize()} event: {event_type}',
                    logger_name=f'{service_name}_service.events',
                    context=event,
                )

                await log_repo.save(log_entry)

    except Exception as e:
        logger.error(f'Failed to process system event from {topic}: {e}')
