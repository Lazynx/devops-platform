import logging
from uuid import UUID

from project_service.application.interfaces.project_repository import IProjectRepository
from project_service.infrastructure.messaging.pending_configs_store import PendingConfigsStore
from project_service.infrastructure.messaging.publisher import ProjectEventPublisher

logger = logging.getLogger(__name__)


class HandleSecretsFailedInteractor:
    def __init__(
        self,
        project_repository: IProjectRepository,
        event_publisher: ProjectEventPublisher,
        pending_configs_store: PendingConfigsStore,
    ):
        self._project_repo = project_repository
        self._event_publisher = event_publisher
        self._pending_configs_store = pending_configs_store

    async def execute(
        self,
        project_id: str,
        error_message: str,
        correlation_id: str,
    ) -> None:
        project_uuid = UUID(project_id)
        correlation_uuid = UUID(correlation_id)

        logger.warning(f'Secrets creation failed for project {project_uuid}: {error_message}')

        project = await self._project_repo.get_by_id(project_uuid)
        if not project:
            logger.error(f'Project {project_uuid} not found')
            return

        project.mark_secrets_failed(error_message)
        project.mark_failed()
        await self._project_repo.update(project)

        self._pending_configs_store.pop(project_uuid)

        await self._event_publisher.publish_project_failed(
            project_id=project_uuid,
            failed_step='secrets',
            error_message=error_message,
            correlation_id=correlation_uuid,
        )
