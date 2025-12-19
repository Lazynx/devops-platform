from uuid import UUID

from faststream.kafka import KafkaBroker


class MessagePublisher:
    def __init__(self, broker: KafkaBroker):
        self._broker = broker
        self._logs_publisher = broker.publisher('service-logs')

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
        
        from datetime import datetime, UTC
        await self._logs_publisher.publish({
            "service": "deployment-service",
            "level": "INFO",
            "message": f"Deployment created: {deployment_id} for project {project_id}",
            "deployment_id": str(deployment_id),
            "project_id": str(project_id),
            "version": version,
            "action": "deployment.created",
            "timestamp": datetime.now(UTC).isoformat(),
            "environment": "development"
        })

    async def publish_deployment_building(
        self,
        deployment_id: UUID,
        project_id: UUID,
    ) -> None:
        await self._broker.publish(
            {
                'deployment_id': str(deployment_id),
                'project_id': str(project_id),
            },
            'deployment.building',
        )

    async def publish_deployment_deploying(
        self,
        deployment_id: UUID,
        project_id: UUID,
    ) -> None:
        await self._broker.publish(
            {
                'deployment_id': str(deployment_id),
                'project_id': str(project_id),
            },
            'deployment.deploying',
        )

    async def publish_deployment_running(
        self,
        deployment_id: UUID,
        project_id: UUID,
        image_url: str,
        deployment_url: str | None = None,
    ) -> None:
        await self._broker.publish(
            {
                'deployment_id': str(deployment_id),
                'project_id': str(project_id),
                'image_url': image_url,
                'deployment_url': deployment_url,
            },
            'deployment.running',
        )

        from datetime import datetime, UTC
        await self._logs_publisher.publish({
            "service": "deployment-service",
            "level": "INFO",
            "message": f"Deployment successful: {deployment_id}",
            "deployment_id": str(deployment_id),
            "project_id": str(project_id),
            "deployment_url": deployment_url,
            "action": "deployment.success",
            "timestamp": datetime.now(UTC).isoformat(),
            "environment": "development"
        })

    async def publish_deployment_failed(
        self,
        deployment_id: UUID,
        project_id: UUID,
        error_message: str,
    ) -> None:
        await self._broker.publish(
            {
                'deployment_id': str(deployment_id),
                'project_id': str(project_id),
                'error_message': error_message,
            },
            'deployment.failed',
        )

        from datetime import datetime, UTC
        await self._logs_publisher.publish({
            "service": "deployment-service",
            "level": "ERROR",
            "message": f"Deployment failed: {deployment_id} - {error_message}",
            "deployment_id": str(deployment_id),
            "project_id": str(project_id),
            "error_message": error_message,
            "action": "deployment.failed",
            "timestamp": datetime.now(UTC).isoformat(),
            "environment": "development"
        })

