from uuid import UUID

from sqlalchemy import delete, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from project_service.application.interfaces.project_repository import IProjectRepository
from project_service.domain.entities import Project, ProjectStatus


class SQLAlchemyProjectRepository(IProjectRepository):
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_id(self, project_id: UUID) -> Project | None:
        result = await self._db.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalars().first()

    async def get_by_owner_id(self, owner_id: UUID) -> list[Project]:
        result = await self._db.execute(
            select(Project)
            .where(Project.owner_id == str(owner_id))
            .where(Project.status != ProjectStatus.deleted)
            .order_by(Project.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_github_repo_url(self, github_repo_url: str) -> Project | None:
        result = await self._db.execute(
            select(Project).where(Project.github_repo_url == github_repo_url)
        )
        return result.scalars().first()

    async def get_by_owner_and_status(
        self,
        owner_id: UUID,
        status: ProjectStatus
    ) -> list[Project]:
        result = await self._db.execute(
            select(Project)
            .where(Project.owner_id == owner_id)
            .where(Project.status == status)
            .order_by(Project.updated_at.desc())
        )
        return list(result.scalars().all())

    async def save(self, project: Project) -> Project:
        self._db.add(project)
        await self._db.commit()
        await self._db.refresh(project)
        return project

    async def update(self, project: Project) -> Project:
        await self._db.commit()
        await self._db.refresh(project)
        return project

    async def delete(self, project_id: UUID) -> None:
        await self._db.execute(
            delete(Project).where(Project.id == project_id)
        )
        await self._db.commit()

    async def exists_by_github_repo_url(self, github_repo_url: str) -> bool:
        result = await self._db.execute(
            select(exists().where(Project.github_repo_url == github_repo_url))
        )
        return result.scalar()
