import logging

from dishka.integrations.faststream import FromDishka, inject
from faststream.kafka import KafkaBroker, KafkaRouter
from pydantic import BaseModel

from project_service.application.interactors.handle_deployment_config_created import HandleDeploymentConfigCreatedInteractor
from project_service.application.interactors.handle_deployment_config_failed import HandleDeploymentConfigFailedInteractor
from project_service.application.interactors.handle_deployment_status_changed import HandleDeploymentStatusChangedInteractor
from project_service.application.interactors.handle_secrets_bulk_created import HandleSecretsBulkCreatedInteractor
from project_service.application.interactors.handle_secrets_failed import HandleSecretsFailedInteractor

logger = logging.getLogger(__name__)

router = KafkaRouter()

DLQ_TOPIC = 'project-service.dlq'


class SecretsBulkCreatedEvent(BaseModel):
    project_id: str
    correlation_id: str


class SecretsFailedEvent(BaseModel):
    project_id: str
    error_message: str
    correlation_id: str


class DeploymentConfigCreatedEvent(BaseModel):
    project_id: str
    config_id: str
    auto_deploy: bool
    correlation_id: str


class DeploymentConfigFailedEvent(BaseModel):
    project_id: str
    error_message: str
    correlation_id: str


class DeploymentStatusEvent(BaseModel):
    deployment_id: str
    project_id: str
    error_message: str | None = None
    image_url: str | None = None
    deployment_url: str | None = None


def _dlq(topic: str, event: BaseModel, error: Exception) -> dict:
    return {'topic': topic, 'event': event.model_dump(), 'error': str(error)}


@router.subscriber('secrets.bulk_created', group_id='project-service-consumers')
@inject
async def handle_secrets_bulk_created(
    event: SecretsBulkCreatedEvent,
    interactor: FromDishka[HandleSecretsBulkCreatedInteractor],
    broker: FromDishka[KafkaBroker],
) -> None:
    logger.info('Received secrets.bulk_created', extra={'project_id': event.project_id})
    try:
        await interactor.execute(project_id=event.project_id, correlation_id=event.correlation_id)
    except Exception as e:
        logger.error('Failed to handle secrets.bulk_created', extra={'project_id': event.project_id, 'error': str(e)}, exc_info=True)
        await broker.publish(_dlq('secrets.bulk_created', event, e), DLQ_TOPIC)


@router.subscriber('secrets.failed', group_id='project-service-consumers')
@inject
async def handle_secrets_failed(
    event: SecretsFailedEvent,
    interactor: FromDishka[HandleSecretsFailedInteractor],
    broker: FromDishka[KafkaBroker],
) -> None:
    logger.info('Received secrets.failed', extra={'project_id': event.project_id})
    try:
        await interactor.execute(project_id=event.project_id, error_message=event.error_message, correlation_id=event.correlation_id)
    except Exception as e:
        logger.error('Failed to handle secrets.failed', extra={'project_id': event.project_id, 'error': str(e)}, exc_info=True)
        await broker.publish(_dlq('secrets.failed', event, e), DLQ_TOPIC)


@router.subscriber('deployment.config_created', group_id='project-service-consumers')
@inject
async def handle_deployment_config_created(
    event: DeploymentConfigCreatedEvent,
    interactor: FromDishka[HandleDeploymentConfigCreatedInteractor],
    broker: FromDishka[KafkaBroker],
) -> None:
    logger.info('Received deployment.config_created', extra={'project_id': event.project_id})
    try:
        await interactor.execute(
            project_id=event.project_id,
            config_id=event.config_id,
            auto_deploy=event.auto_deploy,
            correlation_id=event.correlation_id,
        )
    except Exception as e:
        logger.error('Failed to handle deployment.config_created', extra={'project_id': event.project_id, 'error': str(e)}, exc_info=True)
        await broker.publish(_dlq('deployment.config_created', event, e), DLQ_TOPIC)


@router.subscriber('deployment.config_failed', group_id='project-service-consumers')
@inject
async def handle_deployment_config_failed(
    event: DeploymentConfigFailedEvent,
    interactor: FromDishka[HandleDeploymentConfigFailedInteractor],
    broker: FromDishka[KafkaBroker],
) -> None:
    logger.info('Received deployment.config_failed', extra={'project_id': event.project_id})
    try:
        await interactor.execute(project_id=event.project_id, error_message=event.error_message, correlation_id=event.correlation_id)
    except Exception as e:
        logger.error('Failed to handle deployment.config_failed', extra={'project_id': event.project_id, 'error': str(e)}, exc_info=True)
        await broker.publish(_dlq('deployment.config_failed', event, e), DLQ_TOPIC)


@router.subscriber('deployment.building', group_id='project-service-consumers')
@inject
async def handle_deployment_building(
    event: DeploymentStatusEvent,
    interactor: FromDishka[HandleDeploymentStatusChangedInteractor],
    broker: FromDishka[KafkaBroker],
) -> None:
    logger.info('Received deployment.building', extra={'project_id': event.project_id})
    try:
        await interactor.execute(project_id=event.project_id, status='building')
    except Exception as e:
        logger.error('Failed to handle deployment.building', extra={'project_id': event.project_id, 'error': str(e)}, exc_info=True)
        await broker.publish(_dlq('deployment.building', event, e), DLQ_TOPIC)


@router.subscriber('deployment.deploying', group_id='project-service-consumers')
@inject
async def handle_deployment_deploying(
    event: DeploymentStatusEvent,
    interactor: FromDishka[HandleDeploymentStatusChangedInteractor],
    broker: FromDishka[KafkaBroker],
) -> None:
    logger.info('Received deployment.deploying', extra={'project_id': event.project_id})
    try:
        await interactor.execute(project_id=event.project_id, status='deploying')
    except Exception as e:
        logger.error('Failed to handle deployment.deploying', extra={'project_id': event.project_id, 'error': str(e)}, exc_info=True)
        await broker.publish(_dlq('deployment.deploying', event, e), DLQ_TOPIC)


@router.subscriber('deployment.running', group_id='project-service-consumers')
@inject
async def handle_deployment_running(
    event: DeploymentStatusEvent,
    interactor: FromDishka[HandleDeploymentStatusChangedInteractor],
    broker: FromDishka[KafkaBroker],
) -> None:
    logger.info('Received deployment.running', extra={'project_id': event.project_id})
    try:
        await interactor.execute(project_id=event.project_id, status='running', deployment_url=event.deployment_url)
    except Exception as e:
        logger.error('Failed to handle deployment.running', extra={'project_id': event.project_id, 'error': str(e)}, exc_info=True)
        await broker.publish(_dlq('deployment.running', event, e), DLQ_TOPIC)


@router.subscriber('deployment.failed', group_id='project-service-consumers')
@inject
async def handle_deployment_failed(
    event: DeploymentStatusEvent,
    interactor: FromDishka[HandleDeploymentStatusChangedInteractor],
    broker: FromDishka[KafkaBroker],
) -> None:
    logger.info('Received deployment.failed', extra={'project_id': event.project_id})
    try:
        await interactor.execute(project_id=event.project_id, status='failed', error_message=event.error_message)
    except Exception as e:
        logger.error('Failed to handle deployment.failed', extra={'project_id': event.project_id, 'error': str(e)}, exc_info=True)
        await broker.publish(_dlq('deployment.failed', event, e), DLQ_TOPIC)
