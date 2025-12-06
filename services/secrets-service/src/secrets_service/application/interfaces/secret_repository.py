from abc import ABC, abstractmethod
from uuid import UUID

from secrets_service.domain.entities import SecretMetadata


class SecretRepository(ABC):
    @abstractmethod
    async def save(self, secret: SecretMetadata) -> SecretMetadata:
        pass

    @abstractmethod
    async def get_by_id(self, secret_id: UUID) -> SecretMetadata | None:
        pass

    @abstractmethod
    async def get_by_project_id(self, project_id: UUID) -> list[SecretMetadata]:
        pass

    @abstractmethod
    async def get_by_deployment_id(self, deployment_id: UUID) -> list[SecretMetadata]:
        pass

    @abstractmethod
    async def delete(self, secret_id: UUID) -> None:
        pass
