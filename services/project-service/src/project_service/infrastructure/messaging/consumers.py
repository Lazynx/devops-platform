import logging
from dishka.integrations.faststream import FromDishka, inject
from faststream.kafka import KafkaRouter
from pydantic import BaseModel

from project_service.application.interactors.handle_secrets_bulk_created import (
    HandleSecretsBulkCreatedInteractor,
)
from project_service.application.interactors.handle_secrets_failed import (
    HandleSecretsFailedInteractor,
)
from project_service.application.interactors.handle_deployment_config_created import (
    HandleDeploymentConfigCreatedInteractor,
)
from project_service.application.interactors.handle_deployment_config_failed import (
    HandleDeploymentConfigFailedInteractor,
)
from project_service.application.interactors.handle_deployment_status_changed import (
    HandleDeploymentStatusChangedInteractor,
)

logger = logging.getLogger(__name__)

router = KafkaRouter()


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


@router.subscriber('secrets.bulk_created', group_id='project-service-consumers')
@inject
async def handle_secrets_bulk_created(
    event: SecretsBulkCreatedEvent,
    interactor: FromDishka[HandleSecretsBulkCreatedInteractor],
) -> None:
    logger.info(f'Received secrets.bulk_created for project {event.project_id}')
    await interactor.execute(
        project_id=event.project_id,
        correlation_id=event.correlation_id,
    )


@router.subscriber('secrets.failed', group_id='project-service-consumers')
@inject
async def handle_secrets_failed(
    event: SecretsFailedEvent,
    interactor: FromDishka[HandleSecretsFailedInteractor],
) -> None:
    logger.info(f'Received secrets.failed for project {event.project_id}')
    await interactor.execute(
        project_id=event.project_id,
        error_message=event.error_message,
        correlation_id=event.correlation_id,
    )


@router.subscriber('deployment.config_created', group_id='project-service-consumers')
@inject
async def handle_deployment_config_created(
    event: DeploymentConfigCreatedEvent,
    interactor: FromDishka[HandleDeploymentConfigCreatedInteractor],
) -> None:
    logger.info(f'Received deployment.config_created for project {event.project_id}')
    await interactor.execute(
        project_id=event.project_id,
        config_id=event.config_id,
        auto_deploy=event.auto_deploy,
        correlation_id=event.correlation_id,
    )


@router.subscriber('deployment.config_failed', group_id='project-service-consumers')
@inject
async def handle_deployment_config_failed(
    event: DeploymentConfigFailedEvent,
    interactor: FromDishka[HandleDeploymentConfigFailedInteractor],
) -> None:
    logger.info(f'Received deployment.config_failed for project {event.project_id}')
    await interactor.execute(
        project_id=event.project_id,
        error_message=event.error_message,
        correlation_id=event.correlation_id,
    )


@router.subscriber('deployment.building', group_id='project-service-consumers')
@inject
async def handle_deployment_building(
    event: DeploymentStatusEvent,
    interactor: FromDishka[HandleDeploymentStatusChangedInteractor],
) -> None:
    logger.info(f'Received deployment.building for project {event.project_id}')
    await interactor.execute(project_id=event.project_id, status='building')


@router.subscriber('deployment.deploying', group_id='project-service-consumers')
@inject
async def handle_deployment_deploying(
    event: DeploymentStatusEvent,
    interactor: FromDishka[HandleDeploymentStatusChangedInteractor],
) -> None:
    logger.info(f'Received deployment.deploying for project {event.project_id}')
    await interactor.execute(project_id=event.project_id, status='deploying')


@router.subscriber('deployment.running', group_id='project-service-consumers')
@inject
async def handle_deployment_running(
    event: DeploymentStatusEvent,
    interactor: FromDishka[HandleDeploymentStatusChangedInteractor],
) -> None:
    logger.info(f'Received deployment.running for project {event.project_id}')
    await interactor.execute(
        project_id=event.project_id,
        status='running',
        deployment_url=event.deployment_url,
    )


@router.subscriber('deployment.failed', group_id='project-service-consumers')
@inject
async def handle_deployment_failed(
    event: DeploymentStatusEvent,
    interactor: FromDishka[HandleDeploymentStatusChangedInteractor],
) -> None:
    logger.info(f'Received deployment.failed for project {event.project_id}')
    await interactor.execute(
        project_id=event.project_id,
        status='failed',
        error_message=event.error_message,
    )

