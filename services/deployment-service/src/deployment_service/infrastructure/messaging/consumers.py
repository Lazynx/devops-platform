import logging
from dishka.integrations.faststream import FromDishka, inject
from faststream.kafka import KafkaRouter
from pydantic import BaseModel

from deployment_service.application.interactors.handle_secrets_bulk_created import (
    HandleSecretsBulkCreatedInteractor,
)
from deployment_service.application.interactors.handle_project_deleted import (
    HandleProjectDeletedInteractor,
)

logger = logging.getLogger(__name__)

router = KafkaRouter()


class SecretsBulkCreatedEvent(BaseModel):
    project_id: str
    name: str
    github_repo_url: str
    github_token: str
    start_command: str
    secrets: list[dict]
    deployment_config: dict | None
    auto_deploy: bool
    correlation_id: str


@router.subscriber('secrets.bulk_created', group_id='deployment-service-consumers')
@inject
async def handle_secrets_bulk_created(
    event: SecretsBulkCreatedEvent,
    interactor: FromDishka[HandleSecretsBulkCreatedInteractor],
) -> None:
    logger.info(f'Received secrets.bulk_created for project {event.project_id}')
    await interactor.execute(
        project_id=event.project_id,
        name=event.name,
        github_repo_url=event.github_repo_url,
        github_token=event.github_token,
        start_command=event.start_command,
        secrets=event.secrets,
        deployment_config_data=event.deployment_config,
        auto_deploy=event.auto_deploy,
        correlation_id=event.correlation_id,
    )


class ProjectDeletedEvent(BaseModel):
    project_id: str
    correlation_id: str
    timestamp: str


@router.subscriber('project.deleted', group_id='deployment-service-consumers')
@inject
async def handle_project_deleted(
    event: ProjectDeletedEvent,
    interactor: FromDishka[HandleProjectDeletedInteractor],
) -> None:
    logger.info(f'Received project.deleted for project {event.project_id}')
    await interactor.execute(
        project_id=event.project_id,
        correlation_id=event.correlation_id,
    )
