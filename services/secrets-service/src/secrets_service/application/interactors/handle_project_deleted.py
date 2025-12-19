import logging
from uuid import UUID

from secrets_service.application.interfaces.secret_repository import SecretRepository
from secrets_service.infrastructure.vault.client import VaultClient

logger = logging.getLogger(__name__)


class HandleProjectDeletedInteractor:
    def __init__(
        self,
        repository: SecretRepository,
        vault_client: VaultClient,
    ):
        self._repository = repository
        self._vault_client = vault_client

    async def execute(self, project_id: str, correlation_id: str) -> None:
        logger.info(f"Handling project.deleted for project {project_id}")
        project_uuid = UUID(project_id)

        # 1. Get all secrets for the project
        secrets = await self._repository.get_by_project_id(project_uuid)

        # 2. Delete secrets from Vault and DB
        for secret in secrets:
            try:
                await self._vault_client.delete_secret(secret.vault_path)
            except Exception as e:
                logger.warning(f"Failed to delete secret {secret.vault_path} from Vault: {e}")
            
            await self._repository.delete(secret.id)

        await self._repository._session.commit()
        logger.info(f"Successfully deleted secrets for project {project_id}")
