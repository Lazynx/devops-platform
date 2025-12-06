from uuid import UUID

from faststream.kafka import KafkaBroker


class MessagePublisher:
    def __init__(self, broker: KafkaBroker):
        self._broker = broker

    async def publish_deployment_created(
        self,
        deployment_id: UUID,
        project_id: UUID,
        config_id: UUID,
        version: str,
    ) -> None:
        await self._broker.publish(
            {
                'deployment_id': str(deployment_id),
                'project_id': str(project_id),
                'config_id': str(config_id),
                'version': version,
            },
            'deployment.created',
        )

    async def publish_deployment_started(self, deployment_id: UUID) -> None:
        await self._broker.publish(
            {'deployment_id': str(deployment_id)},
            'deployment.started',
        )

    async def publish_deployment_completed(
        self,
        deployment_id: UUID,
        image_url: str
    ) -> None:
        await self._broker.publish(
            {
                'deployment_id': str(deployment_id),
                'image_url': image_url,
            },
            'deployment.completed',
        )

    async def publish_deployment_failed(
        self,
        deployment_id: UUID,
        error_message: str
    ) -> None:
        await self._broker.publish(
            {
                'deployment_id': str(deployment_id),
                'error_message': error_message,
            },
            'deployment.failed',
        )
