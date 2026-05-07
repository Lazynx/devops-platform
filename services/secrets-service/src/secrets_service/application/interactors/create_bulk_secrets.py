import asyncio
from uuid import UUID

from secrets_service.application.dtos import CreateBulkSecretsDTO, SecretDTO
from secrets_service.application.interfaces.secret_repository import SecretRepository
from secrets_service.domain.entities import SecretMetadata
from secrets_service.infrastructure.messaging.publisher import SecretEventPublisher
from secrets_service.infrastructure.vault.client import VaultClient


class CreateBulkSecretsInteractor:
    def __init__(self, repository: SecretRepository, vault_client: VaultClient, publisher: SecretEventPublisher):
        self._repository = repository
        self._vault_client = vault_client
        self._publisher = publisher

    async def execute(self, dto: CreateBulkSecretsDTO) -> list[SecretDTO]:
        vault_path = self._build_vault_path(dto.project_id, dto.deployment_id)

        all_secrets_data = {s.key: s.value for s in dto.secrets}

        await self._vault_client.write_secret(vault_path, all_secrets_data)

        metadata_list = []
        for secret_item in dto.secrets:
            metadata = SecretMetadata(
                project_id=dto.project_id,
                deployment_id=dto.deployment_id,
                key=secret_item.key,
                vault_path=vault_path,
                secret_type=secret_item.secret_type,
                description=secret_item.description,
            )
            metadata_list.append(metadata)

        metadata_list = await self._repository.save_many(metadata_list)

        policy_name = f"project-{dto.project_id}-read"
        policy_rules = f"""
path "secret/data/projects/{dto.project_id}/*" {{
  capabilities = ["read"]
}}
"""
        await self._vault_client.create_policy(policy_name, policy_rules)

        publish_tasks = [
            self._publisher.publish_secret_created(
                metadata.id, metadata.project_id, metadata.deployment_id, metadata.key
            )
            for metadata in metadata_list
        ]
        await asyncio.gather(*publish_tasks)

        return [
            SecretDTO(
                id=metadata.id,
                project_id=metadata.project_id,
                deployment_id=metadata.deployment_id,
                key=metadata.key,
                secret_type=metadata.secret_type,
                vault_path=metadata.vault_path,
                description=metadata.description,
            )
            for metadata in metadata_list
        ]

    def _build_vault_path(self, project_id: UUID, deployment_id: UUID | None) -> str:
        if deployment_id:
            return f'projects/{project_id}/deployments/{deployment_id}'
        return f'projects/{project_id}'
