import logging
from uuid import UUID

from secrets_service.application.dtos import CreateBulkSecretsDTO, SecretItemDTO
from secrets_service.application.interactors.create_bulk_secrets import CreateBulkSecretsInteractor
from secrets_service.infrastructure.messaging.publisher import SecretEventPublisher

logger = logging.getLogger(__name__)


class HandleProjectCreatedWithSecretsInteractor:
    def __init__(
        self,
        create_bulk_secrets_interactor: CreateBulkSecretsInteractor,
        publisher: SecretEventPublisher,
    ):
        self._create_bulk_secrets_interactor = create_bulk_secrets_interactor
        self._publisher = publisher

    async def execute(
        self,
        project_id: str,
        name: str,
        github_repo_url: str,
        github_token: str,
        start_command: str,
        secrets: list[dict],
        deployment_config: dict | None,
        auto_deploy: bool,
        correlation_id: str,
    ) -> None:
        logger.info(f"Handling project.created_with_secrets for project {project_id}")

        created_secrets = []
        if secrets:
            dto = CreateBulkSecretsDTO(
                project_id=UUID(project_id),
                deployment_id=None,
                secrets=[
                    SecretItemDTO(
                        key=s['key'],
                        value=s['value'],
                        secret_type=s['secret_type'],
                        description=s.get('description'),
                    )
                    for s in secrets
                ],
            )
            created_secrets = await self._create_bulk_secrets_interactor.execute(dto)

        secrets_data = [
            {
                'key': s.key,
                'vault_path': s.vault_path,
            }
            for s in created_secrets
        ]

        await self._publisher.publish_secrets_bulk_created(
            project_id=UUID(project_id),
            name=name,
            github_repo_url=github_repo_url,
            github_token=github_token,
            start_command=start_command,
            secrets=secrets_data,
            deployment_config=deployment_config,
            auto_deploy=auto_deploy,
            correlation_id=correlation_id,
        )
