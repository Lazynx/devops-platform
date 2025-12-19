from uuid import UUID

from faststream.kafka import KafkaBroker
from pydantic import BaseModel


class SecretCreatedEvent(BaseModel):
    secret_id: str
    project_id: str
    deployment_id: str | None
    key: str


class SecretUpdatedEvent(BaseModel):
    secret_id: str
    project_id: str
    key: str


class SecretDeletedEvent(BaseModel):
    secret_id: str
    project_id: str
    key: str


class SecretsBulkCreatedEvent(BaseModel):
    project_id: str
    name: str
    github_repo_url: str
    github_token: str
    start_command: str
    secrets: list[dict]
    deployment_config: dict | None
    auto_deploy: bool
    correlation_id: str


class SecretEventPublisher:
    def __init__(self, broker: KafkaBroker):
        self._secret_created_publisher = broker.publisher('secret.created')
        self._secret_updated_publisher = broker.publisher('secret.updated')
        self._secret_deleted_publisher = broker.publisher('secret.deleted')
        self._secrets_bulk_created_publisher = broker.publisher('secrets.bulk_created')
        self._logs_publisher = broker.publisher('service-logs')

    async def publish_secret_created(
        self, secret_id: UUID, project_id: UUID, deployment_id: UUID | None, key: str
    ) -> None:
        event = SecretCreatedEvent(
            secret_id=str(secret_id),
            project_id=str(project_id),
            deployment_id=str(deployment_id) if deployment_id else None,
            key=key,
        )
        await self._secret_created_publisher.publish(event)

        from datetime import datetime, UTC
        await self._logs_publisher.publish({
            "service": "secrets-service",
            "level": "INFO",
            "message": f"Secret created: {key} for project {project_id}",
            "secret_id": str(secret_id),
            "project_id": str(project_id),
            "key": key,
            "action": "secret.created",
            "timestamp": datetime.now(UTC).isoformat(),
            "environment": "development"
        })

    async def publish_secret_updated(self, secret_id: UUID, project_id: UUID, key: str) -> None:
        event = SecretUpdatedEvent(
            secret_id=str(secret_id),
            project_id=str(project_id),
            key=key,
        )
        await self._secret_updated_publisher.publish(event)

    async def publish_secret_deleted(self, secret_id: UUID, project_id: UUID, key: str) -> None:
        event = SecretDeletedEvent(
            secret_id=str(secret_id),
            project_id=str(project_id),
            key=key,
        )
        await self._secret_deleted_publisher.publish(event)

        from datetime import datetime, UTC
        await self._logs_publisher.publish({
            "service": "secrets-service",
            "level": "INFO",
            "message": f"Secret deleted: {key} for project {project_id}",
            "secret_id": str(secret_id),
            "project_id": str(project_id),
            "key": key,
            "action": "secret.deleted",
            "timestamp": datetime.now(UTC).isoformat(),
            "environment": "development"
        })

    async def publish_secrets_bulk_created(
        self,
        project_id: UUID,
        name: str,
        github_repo_url: str,
        github_token: str,
        start_command: str,
        secrets: list[dict],
        deployment_config: dict | None,
        auto_deploy: bool,
        correlation_id: str,
    ) -> None:
        event = SecretsBulkCreatedEvent(
            project_id=str(project_id),
            name=name,
            github_repo_url=github_repo_url,
            github_token=github_token,
            start_command=start_command,
            secrets=secrets,
            deployment_config=deployment_config,
            auto_deploy=auto_deploy,
            correlation_id=correlation_id,
        )
        await self._secrets_bulk_created_publisher.publish(event)
