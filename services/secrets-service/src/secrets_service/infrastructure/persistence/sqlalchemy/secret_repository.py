from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from secrets_service.application.interfaces.secret_repository import SecretRepository
from secrets_service.domain.entities import SecretMetadata


class SqlAlchemySecretRepository(SecretRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, secret: SecretMetadata) -> SecretMetadata:
        self._session.add(secret)
        await self._session.flush()
        await self._session.refresh(secret)
        return secret

    async def get_by_id(self, secret_id: UUID) -> SecretMetadata | None:
        result = await self._session.execute(select(SecretMetadata).where(SecretMetadata.id == secret_id))
        return result.scalar_one_or_none()

    async def get_by_project_id(self, project_id: UUID) -> list[SecretMetadata]:
        result = await self._session.execute(
            select(SecretMetadata).where(SecretMetadata.project_id == project_id)
        )
        return list(result.scalars().all())

    async def get_by_deployment_id(self, deployment_id: UUID) -> list[SecretMetadata]:
        result = await self._session.execute(
            select(SecretMetadata).where(SecretMetadata.deployment_id == deployment_id)
        )
        return list(result.scalars().all())

    async def delete(self, secret_id: UUID) -> None:
        query = delete(SecretMetadata).where(SecretMetadata.id == secret_id)
        await self._session.execute(query)


