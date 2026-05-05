import logging

from dishka.integrations.faststream import FromDishka, inject
from faststream.kafka import KafkaBroker, KafkaRouter
from pydantic import BaseModel

from secrets_service.application.interactors.handle_project_created_with_secrets import (
    HandleProjectCreatedWithSecretsInteractor,
)
from secrets_service.application.interactors.handle_project_deleted import (
    HandleProjectDeletedInteractor,
)

logger = logging.getLogger(__name__)

router = KafkaRouter()

DLQ_TOPIC = 'secrets-service.dlq'


class ProjectCreatedWithSecretsEvent(BaseModel):
    project_id: str
    owner_id: str
    name: str
    github_repo_url: str
    github_token: str
    start_command: str
    framework: str | None
    secrets: list[dict]
    deployment_config: dict | None
    auto_deploy: bool
    correlation_id: str
    timestamp: str


@router.subscriber('project.created_with_secrets', group_id='secrets-service-consumers')
@inject
async def handle_project_created_with_secrets(
    event: ProjectCreatedWithSecretsEvent,
    interactor: FromDishka[HandleProjectCreatedWithSecretsInteractor],
    broker: FromDishka[KafkaBroker],
) -> None:
    logger.info('Received project.created_with_secrets', extra={'project_id': event.project_id, 'correlation_id': event.correlation_id})
    try:
        await interactor.execute(
            project_id=event.project_id,
            name=event.name,
            github_repo_url=event.github_repo_url,
            github_token=event.github_token,
            start_command=event.start_command,
            secrets=event.secrets,
            deployment_config=event.deployment_config,
            auto_deploy=event.auto_deploy,
            correlation_id=event.correlation_id,
        )
    except Exception as e:
        logger.error(
            'Failed to handle project.created_with_secrets',
            extra={'project_id': event.project_id, 'error': str(e)},
            exc_info=True,
        )
        await broker.publish(
            {'topic': 'project.created_with_secrets', 'event': event.model_dump(), 'error': str(e)},
            DLQ_TOPIC,
        )


class ProjectDeletedEvent(BaseModel):
    project_id: str
    correlation_id: str
    timestamp: str


@router.subscriber('project.deleted', group_id='secrets-service-consumers')
@inject
async def handle_project_deleted(
    event: ProjectDeletedEvent,
    interactor: FromDishka[HandleProjectDeletedInteractor],
    broker: FromDishka[KafkaBroker],
) -> None:
    logger.info('Received project.deleted', extra={'project_id': event.project_id, 'correlation_id': event.correlation_id})
    try:
        await interactor.execute(
            project_id=event.project_id,
            correlation_id=event.correlation_id,
        )
    except Exception as e:
        logger.error(
            'Failed to handle project.deleted',
            extra={'project_id': event.project_id, 'error': str(e)},
            exc_info=True,
        )
        await broker.publish(
            {'topic': 'project.deleted', 'event': event.model_dump(), 'error': str(e)},
            DLQ_TOPIC,
        )
