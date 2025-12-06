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


class SecretEventPublisher:
    def __init__(self, broker: KafkaBroker):
        self._secret_created_publisher = broker.publisher('secret.created')
        self._secret_updated_publisher = broker.publisher('secret.updated')
        self._secret_deleted_publisher = broker.publisher('secret.deleted')

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
