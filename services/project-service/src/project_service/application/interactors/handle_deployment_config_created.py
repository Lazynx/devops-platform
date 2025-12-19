import logging
from uuid import UUID

from project_service.application.interfaces.project_repository import IProjectRepository
from project_service.infrastructure.messaging.publisher import ProjectEventPublisher

logger = logging.getLogger(__name__)


class HandleDeploymentConfigCreatedInteractor:
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
        config_id: str,
        auto_deploy: bool,
        correlation_id: str,
    ) -> None:
        project_uuid = UUID(project_id)
        config_uuid = UUID(config_id)
        correlation_uuid = UUID(correlation_id)

        logger.info(f'Deployment config created for project {project_uuid}: {config_uuid}')

        project = await self._project_repo.get_by_id(project_uuid)
        if not project:
            logger.error(f'Project {project_uuid} not found')
            return

        project.mark_deployment_ready(config_uuid)
        project.mark_ready()
        await self._project_repo.update(project)

        await self._event_publisher.publish_project_ready(
            project_id=project_uuid,
            deployment_config_id=config_uuid,
            auto_deploy=auto_deploy,
            correlation_id=correlation_uuid,
        )
