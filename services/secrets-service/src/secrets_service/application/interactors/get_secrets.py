from uuid import UUID

from secrets_service.application.dtos import SecretDTO, SecretWithValueDTO
from secrets_service.application.interfaces.secret_repository import SecretRepository
from secrets_service.infrastructure.vault.client import VaultClient


class GetSecretsByProjectInteractor:
    def __init__(self, repository: SecretRepository):
        self._repository = repository

    async def execute(self, project_id: UUID) -> list[SecretDTO]:
        secrets = await self._repository.get_by_project_id(project_id)
        return [
            SecretDTO(
                id=secret.id,
                project_id=secret.project_id,
                deployment_id=secret.deployment_id,
                key=secret.key,
                secret_type=secret.secret_type,
                vault_path=secret.vault_path,
                description=secret.description,
            )
            for secret in secrets
        ]


class GetSecretsByDeploymentInteractor:
    def __init__(self, repository: SecretRepository, vault_client: VaultClient):
        self._repository = repository
        self._vault_client = vault_client

    async def execute(self, deployment_id: UUID) -> list[SecretWithValueDTO]:
        secrets = await self._repository.get_by_deployment_id(deployment_id)
        result = []

        for secret in secrets:
            vault_data = await self._vault_client.read_secret(secret.vault_path)
            result.append(
                SecretWithValueDTO(
                    id=secret.id,
                    project_id=secret.project_id,
                    deployment_id=secret.deployment_id,
                    key=secret.key,
                    value=vault_data['value'],
                    secret_type=secret.secret_type,
                    description=secret.description,
                )
            )

        return result


class GetSecretValueInteractor:
    def __init__(self, repository: SecretRepository, vault_client: VaultClient):
        self._repository = repository
        self._vault_client = vault_client

    async def execute(self, secret_id: UUID) -> SecretWithValueDTO:
        secret = await self._repository.get_by_id(secret_id)
        if not secret:
            raise ValueError(f'Secret {secret_id} not found')

        vault_data = await self._vault_client.read_secret(secret.vault_path)

        return SecretWithValueDTO(
            id=secret.id,
            project_id=secret.project_id,
            deployment_id=secret.deployment_id,
            key=secret.key,
            value=vault_data['value'],
            secret_type=secret.secret_type,
            description=secret.description,
        )
