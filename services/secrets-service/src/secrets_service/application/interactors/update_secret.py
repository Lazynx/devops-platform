from secrets_service.application.dtos import SecretDTO, UpdateSecretDTO
from secrets_service.application.interfaces.secret_repository import SecretRepository
from secrets_service.infrastructure.messaging.publisher import SecretEventPublisher
from secrets_service.infrastructure.vault.client import VaultClient


class UpdateSecretInteractor:
    def __init__(self, repository: SecretRepository, vault_client: VaultClient, publisher: SecretEventPublisher):
        self._repository = repository
        self._vault_client = vault_client
        self._publisher = publisher

    async def execute(self, dto: UpdateSecretDTO) -> SecretDTO:
        secret = await self._repository.get_by_id(dto.secret_id)
        if not secret:
            raise ValueError(f'Secret {dto.secret_id} not found')

        await self._vault_client.write_secret(secret.vault_path, {'value': dto.value})

        if dto.description is not None:
            secret.description = dto.description
            await self._repository.save(secret)

        await self._publisher.publish_secret_updated(secret.id, secret.project_id, secret.key)

        return SecretDTO(
            id=secret.id,
            project_id=secret.project_id,
            deployment_id=secret.deployment_id,
            key=secret.key,
            secret_type=secret.secret_type,
            vault_path=secret.vault_path,
            description=secret.description,
        )
