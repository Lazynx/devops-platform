from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from deployment_service.application.interfaces import IDeploymentRepository
from deployment_service.domain.entities import Deployment


class DeploymentRepository(IDeploymentRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, deployment: Deployment) -> Deployment:
        self._session.add(deployment)
        await self._session.commit()
        await self._session.refresh(deployment)
        return deployment

    async def get_by_id(self, deployment_id: UUID) -> Deployment | None:
        result = await self._session.execute(
            select(Deployment).where(Deployment.id == deployment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_config_id(self, config_id: UUID) -> list[Deployment]:
        result = await self._session.execute(
            select(Deployment)
            .where(Deployment.config_id == config_id)
            .order_by(Deployment.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_latest_by_config(self, config_id: UUID) -> Deployment | None:
        result = await self._session.execute(
            select(Deployment)
            .where(Deployment.config_id == config_id)
            .order_by(Deployment.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
