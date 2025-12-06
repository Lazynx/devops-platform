from abc import ABC, abstractmethod
from uuid import UUID

from project_service.domain.entities import Project, ProjectStatus


class IProjectRepository(ABC):
    @abstractmethod
    async def get_by_id(self, project_id: UUID) -> Project | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_owner_id(self, owner_id: UUID) -> list[Project]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_github_repo_url(self, github_repo_url: str) -> Project | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_owner_and_status(
        self,
        owner_id: UUID,
        status: ProjectStatus
    ) -> list[Project]:
        raise NotImplementedError

    @abstractmethod
    async def save(self, project: Project) -> Project:
        raise NotImplementedError

    @abstractmethod
    async def update(self, project: Project) -> Project:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, project_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def exists_by_github_repo_url(self, github_repo_url: str) -> bool:
        raise NotImplementedError
