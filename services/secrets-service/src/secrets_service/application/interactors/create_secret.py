from uuid import UUID

from secrets_service.application.dtos import CreateSecretDTO, SecretDTO
from secrets_service.application.interfaces.secret_repository import SecretRepository
from secrets_service.domain.entities import SecretMetadata
from secrets_service.infrastructure.messaging.publisher import SecretEventPublisher
from secrets_service.infrastructure.vault.client import VaultClient


class CreateSecretInteractor:
    def __init__(self, repository: SecretRepository, vault_client: VaultClient, publisher: SecretEventPublisher):
        self._repository = repository
        self._vault_client = vault_client
        self._publisher = publisher

    async def execute(self, dto: CreateSecretDTO) -> SecretDTO:
        vault_path = self._build_vault_path(dto.project_id, dto.deployment_id, dto.key)

        await self._vault_client.write_secret(vault_path, {'value': dto.value})

        metadata = SecretMetadata(
            project_id=dto.project_id,
            deployment_id=dto.deployment_id,
            key=dto.key,
            vault_path=vault_path,
            secret_type=dto.secret_type,
            description=dto.description,
        )

        saved = await self._repository.save(metadata)

        await self._publisher.publish_secret_created(
            saved.id, saved.project_id, saved.deployment_id, saved.key
        )

        return SecretDTO(
            id=saved.id,
            project_id=saved.project_id,
            deployment_id=saved.deployment_id,
            key=saved.key,
            secret_type=saved.secret_type,
            vault_path=saved.vault_path,
            description=saved.description,
        )

    def _build_vault_path(self, project_id: UUID, deployment_id: UUID | None, key: str) -> str:
        if deployment_id:
            return f'projects/{project_id}/deployments/{deployment_id}/{key}'
        return f'projects/{project_id}/{key}'
