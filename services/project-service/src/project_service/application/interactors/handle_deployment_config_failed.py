import logging
from uuid import UUID

from project_service.application.interfaces.project_repository import IProjectRepository
from project_service.infrastructure.messaging.publisher import ProjectEventPublisher

logger = logging.getLogger(__name__)


class HandleDeploymentConfigFailedInteractor:
    def __init__(
        self,
        project_repository: IProjectRepository,
        event_publisher: ProjectEventPublisher,
    ):
        self._project_repo = project_repository
        self._event_publisher = event_publisher

    async def execute(
        self,
        project_id: str,
        error_message: str,
        correlation_id: str,
    ) -> None:
        project_uuid = UUID(project_id)
        correlation_uuid = UUID(correlation_id)

        logger.warning(f'Deployment config failed for project {project_uuid}: {error_message}')

        project = await self._project_repo.get_by_id(project_uuid)
        if not project:
            logger.error(f'Project {project_uuid} not found')
            return

        project.mark_deployment_failed(error_message)
        project.mark_failed()
        await self._project_repo.update(project)

        await self._event_publisher.publish_project_failed(
            project_id=project_uuid,
            failed_step='deployment',
            error_message=error_message,
            correlation_id=correlation_uuid,
        )
