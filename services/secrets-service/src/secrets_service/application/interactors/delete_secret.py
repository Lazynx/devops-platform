from uuid import UUID

from secrets_service.application.interfaces.secret_repository import SecretRepository
from secrets_service.infrastructure.messaging.publisher import SecretEventPublisher
from secrets_service.infrastructure.vault.client import VaultClient


class DeleteSecretInteractor:
    def __init__(self, repository: SecretRepository, vault_client: VaultClient, publisher: SecretEventPublisher):
        self._repository = repository
        self._vault_client = vault_client
        self._publisher = publisher

    async def execute(self, secret_id: UUID) -> None:
        secret = await self._repository.get_by_id(secret_id)
        if not secret:
            raise ValueError(f'Secret {secret_id} not found')

        await self._vault_client.delete_secret(secret.vault_path)
        await self._repository.delete(secret_id)

        await self._publisher.publish_secret_deleted(secret.id, secret.project_id, secret.key)
