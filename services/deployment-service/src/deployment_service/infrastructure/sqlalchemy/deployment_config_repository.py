from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from deployment_service.application.interfaces import IDeploymentConfigRepository
from deployment_service.domain.entities import DeploymentConfig


class DeploymentConfigRepository(IDeploymentConfigRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, config: DeploymentConfig) -> DeploymentConfig:
        self._session.add(config)
        await self._session.commit()
        await self._session.refresh(config)
        return config

    async def get_by_id(self, config_id: UUID) -> DeploymentConfig | None:
        result = await self._session.execute(
            select(DeploymentConfig).where(DeploymentConfig.id == config_id)
        )
        return result.scalar_one_or_none()

    async def get_by_project_id(self, project_id: UUID) -> list[DeploymentConfig]:
        result = await self._session.execute(
            select(DeploymentConfig).where(DeploymentConfig.project_id == project_id)
        )
        return list(result.scalars().all())

    async def get_by_project_and_environment(
        self, project_id: UUID, environment: str
    ) -> DeploymentConfig | None:
        result = await self._session.execute(
            select(DeploymentConfig).where(
                DeploymentConfig.project_id == project_id,
                DeploymentConfig.environment == environment,
            )
        )
        return result.scalar_one_or_none()
