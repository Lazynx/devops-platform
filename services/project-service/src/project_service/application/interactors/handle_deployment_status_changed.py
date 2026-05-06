import logging
from uuid import UUID

from project_service.application.interfaces.project_repository import IProjectRepository
from project_service.domain.entities import ProjectStatus

logger = logging.getLogger(__name__)


class HandleDeploymentStatusChangedInteractor:
    def __init__(self, project_repository: IProjectRepository):
        self._project_repo = project_repository

    async def execute(
        self,
        project_id: str,
        status: str,
        error_message: str | None = None,
        deployment_url: str | None = None,
    ) -> None:
        logger.info(f"Updating project {project_id} deployment status to {status}")

        project = await self._project_repo.get_by_id(UUID(project_id))
        if not project:
            logger.error(f"Project {project_id} not found")
            return

        if status == 'building' or status == 'deploying':
            project.status = ProjectStatus.deployment_pending
        elif status == 'running':
            project.status = ProjectStatus.active
            if deployment_url:
                project.deployment_url = deployment_url
        elif status == 'failed':
            project.mark_failed()
            if error_message:
                project.last_error_message = error_message
                project.last_error_step = 'deployment'

        await self._project_repo.save(project)
        logger.info(f"Project {project_id} status updated to {project.status}")
