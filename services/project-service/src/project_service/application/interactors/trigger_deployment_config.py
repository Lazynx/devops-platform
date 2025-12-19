import logging
from uuid import UUID

from project_service.application.dtos import DeploymentConfigDTO
from project_service.application.exceptions import (
    DeploymentConfigCreationError,
    DeploymentServiceError,
    ProjectNotFoundError,
)
from project_service.application.interfaces.project_repository import IProjectRepository
from project_service.infrastructure.deployment_service import DeploymentServiceClient
from project_service.infrastructure.messaging.publisher import ProjectEventPublisher

logger = logging.getLogger(__name__)


class TriggerDeploymentConfigInteractor:
    def __init__(
        self,
        repository: IProjectRepository,
        deployment_client: DeploymentServiceClient,
        publisher: ProjectEventPublisher,
    ):
        self._repository = repository
        self._deployment_client = deployment_client
        self._publisher = publisher

    async def execute(
        self,
        project_id: UUID,
        deployment_config: DeploymentConfigDTO,
        user_access_token: str,
        correlation_id: UUID,
    ) -> UUID:
        project = await self._repository.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundError(project_id)

        project.mark_deployment_creating()
        await self._repository.update(project)

        try:
            config_id = await self._deployment_client.create_deployment_config(
                user_access_token=user_access_token,
                project_id=project_id,
                github_repo_url=project.github_repo_url,
                config=deployment_config,
            )

            project.mark_deployment_ready(config_id)
            project.mark_ready()
            await self._repository.update(project)

            await self._publisher.publish_project_ready(
                project_id=project_id,
                deployment_config_id=config_id,
                auto_deploy=False,
                correlation_id=correlation_id,
            )

            return config_id

        except DeploymentServiceError as e:
            error_message = e.message
            logger.error(f"Deployment config creation failed for project {project_id}: {error_message}")

            project.mark_deployment_failed(error_message)
            project.mark_failed()
            await self._repository.update(project)

            await self._publisher.publish_project_failed(
                project_id=project_id,
                failed_step='deployment',
                error_message=error_message,
                correlation_id=correlation_id,
            )

            raise DeploymentConfigCreationError(project_id, error_message)
