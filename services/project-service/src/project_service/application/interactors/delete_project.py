from uuid import UUID, uuid4

from project_service.application.interfaces.project_repository import IProjectRepository
from project_service.infrastructure.messaging.publisher import ProjectEventPublisher


class DeleteProjectInteractor:
    def __init__(
        self,
        project_repo: IProjectRepository,
        publisher: ProjectEventPublisher,
    ):
        self._project_repo = project_repo
        self._publisher = publisher

    async def execute(self, project_id: UUID) -> None:
        project = await self._project_repo.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        await self._project_repo.delete(project_id)
        await self._project_repo._session.commit()

        await self._publisher.publish_project_deleted(
            project_id=project_id,
            correlation_id=uuid4(),
        )
