import logging
from uuid import UUID

from faststream.kafka import KafkaBroker

from deployment_service.application.dtos import ProjectCreatedEventDTO

logger = logging.getLogger(__name__)

broker = KafkaBroker()


@broker.subscriber('project.created')
async def handle_project_created(event: dict) -> None:
    logger.info(f'Received project.created event: {event}')

    try:
        dto = ProjectCreatedEventDTO(
            project_id=UUID(event['project_id']),
            owner_id=UUID(event['owner_id']),
            name=event['name'],
            github_repo_url=event['github_repo_url'],
            framework=event.get('framework'),
        )

        logger.info(f'Project created: {dto.project_id} by user {dto.owner_id}')

    except Exception as e:
        logger.error(f'Failed to process project.created event: {e}')
        raise


@broker.subscriber('secret.created')
async def handle_secret_created(event: dict) -> None:
    logger.info(f'Received secret.created event: {event}')

    try:
        secret_id = UUID(event['secret_id'])
        project_id = UUID(event['project_id'])
        deployment_id = UUID(event['deployment_id']) if event.get('deployment_id') else None

        logger.info(f'Secret {secret_id} created for project {project_id}, deployment {deployment_id}')

    except Exception as e:
        logger.error(f'Failed to process secret.created event: {e}')
        raise
