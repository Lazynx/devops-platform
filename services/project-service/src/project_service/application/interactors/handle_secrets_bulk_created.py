import logging
from uuid import UUID

from project_service.application.interfaces.project_repository import IProjectRepository
from project_service.infrastructure.deployment_service import DeploymentServiceClient
from project_service.infrastructure.messaging.pending_configs_store import PendingConfigsStore
from project_service.infrastructure.messaging.publisher import ProjectEventPublisher

logger = logging.getLogger(__name__)


class HandleSecretsBulkCreatedInteractor:
    def __init__(
        self,
        project_repository: IProjectRepository,
        event_publisher: ProjectEventPublisher,
        deployment_client: DeploymentServiceClient,
        pending_configs_store: PendingConfigsStore,
    ):
        self._project_repo = project_repository
        self._event_publisher = event_publisher
        self._deployment_client = deployment_client
        self._pending_configs_store = pending_configs_store

    async def execute(
        self,
        project_id: str,
        correlation_id: str,
    ) -> None:
        project_uuid = UUID(project_id)
        correlation_uuid = UUID(correlation_id)

        logger.info(f'Processing secrets.bulk_created for project {project_uuid}')

        project = await self._project_repo.get_by_id(project_uuid)
        if not project:
            logger.error(f'Project {project_uuid} not found')
            return

        project.mark_secrets_ready()
        await self._project_repo.update(project)

        pending = self._pending_configs_store.pop(project_uuid)
        if pending:
            deployment_config, user_token, auto_deploy = pending
            try:
                project.mark_deployment_creating()
                await self._project_repo.update(project)

                config_id = await self._deployment_client.create_deployment_config(
                    user_access_token=user_token,
                    project_id=project_uuid,
                    github_repo_url=project.github_repo_url,
                    config=deployment_config,
                )

                project.mark_deployment_ready(config_id)
                project.mark_ready()
                await self._project_repo.update(project)

                await self._event_publisher.publish_project_ready(
                    project_id=project_uuid,
                    deployment_config_id=config_id,
                    auto_deploy=auto_deploy,
                    correlation_id=correlation_uuid,
                )

            except Exception as e:
                logger.error(f'Failed to create deployment config for project {project_uuid}: {e}')
                project.mark_deployment_failed(str(e))
                project.mark_failed()
                await self._project_repo.update(project)

                await self._event_publisher.publish_project_failed(
                    project_id=project_uuid,
                    failed_step='deployment',
                    error_message=str(e),
                    correlation_id=correlation_uuid,
                )
        else:
            project.mark_ready()
            await self._project_repo.update(project)

            await self._event_publisher.publish_project_ready(
                project_id=project_uuid,
                deployment_config_id=None,
                auto_deploy=False,
                correlation_id=correlation_uuid,
            )
