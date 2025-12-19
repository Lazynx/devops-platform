import logging
from datetime import datetime, UTC
from uuid import UUID, uuid4

from faststream.kafka import KafkaBroker
from pydantic import BaseModel

from project_service.application.dtos import ProjectSecretDTO, DeploymentConfigDTO

logger = logging.getLogger(__name__)


class ProjectCreatedWithSecretsEvent(BaseModel):
    project_id: str
    owner_id: str
    name: str
    github_repo_url: str
    github_token: str
    start_command: str
    framework: str | None
    secrets: list[dict]
    deployment_config: dict | None
    auto_deploy: bool
    correlation_id: str
    timestamp: str


class ProjectReadyEvent(BaseModel):
    project_id: str
    deployment_config_id: str | None
    auto_deploy: bool
    correlation_id: str
    timestamp: str


class ProjectFailedEvent(BaseModel):
    project_id: str
    failed_step: str
    error_message: str
    correlation_id: str
    timestamp: str


class ProjectEventPublisher:
    def __init__(self, broker: KafkaBroker):
        self._project_created_publisher = broker.publisher('project.created')
        self._project_created_with_secrets_publisher = broker.publisher('project.created_with_secrets')
        self._project_ready_publisher = broker.publisher('project.ready')
        self._project_failed_publisher = broker.publisher('project.failed')
        self._project_deleted_publisher = broker.publisher('project.deleted')
        self._logs_publisher = broker.publisher('service-logs')

    async def publish_project_created(
        self,
        project_id: UUID,
        owner_id: UUID,
        name: str,
        github_repo_url: str,
        framework: str | None,
    ) -> None:
        await self._project_created_publisher.publish(
            {
                'project_id': str(project_id),
                'owner_id': str(owner_id),
                'name': name,
                'github_repo_url': github_repo_url,
                'framework': framework,
            },
        )
        
        await self._logs_publisher.publish({
            "service": "project-service",
            "level": "INFO",
            "message": f"Project created: {name}",
            "project_id": str(project_id),
            "owner_id": str(owner_id),
            "action": "project.created",
            "timestamp": datetime.now(UTC).isoformat(),
            "environment": "development"
        })

    async def publish_project_created_with_secrets(
        self,
        project_id: UUID,
        owner_id: UUID,
        name: str,
        github_repo_url: str,
        github_token: str,
        start_command: str,
        framework: str | None,
        secrets: list[ProjectSecretDTO],
        deployment_config: DeploymentConfigDTO | None,
        auto_deploy: bool,
        correlation_id: UUID | None = None,
    ) -> UUID:
        corr_id = correlation_id or uuid4()
        
        secrets_data = [
            {
                'key': s.key,
                'value': s.value,
                'secret_type': s.secret_type,
                'description': s.description,
            }
            for s in secrets
        ] if secrets else []
        
        config_data = None
        if deployment_config:
            config_data = {
                'environment': deployment_config.environment,
                'instance_count': deployment_config.instance_count,
                'cpu_limit': deployment_config.cpu_limit,
                'memory_limit': deployment_config.memory_limit,
                'port': deployment_config.port,
                'health_check_path': deployment_config.health_check_path,
                'dockerfile_path': deployment_config.dockerfile_path,
                'docker_build_context': deployment_config.docker_build_context,
                'auto_scaling_enabled': deployment_config.auto_scaling_enabled,
                'min_instances': deployment_config.min_instances,
                'max_instances': deployment_config.max_instances,
            }

        event = ProjectCreatedWithSecretsEvent(
            project_id=str(project_id),
            owner_id=str(owner_id),
            name=name,
            github_repo_url=github_repo_url,
            github_token=github_token,
            start_command=start_command,
            framework=framework,
            secrets=secrets_data,
            deployment_config=config_data,
            auto_deploy=auto_deploy,
            correlation_id=str(corr_id),
            timestamp=datetime.now(UTC).isoformat(),
        )

        logger.info(f'Publishing project.created_with_secrets for project {project_id} with {len(secrets_data)} secrets')
        await self._project_created_with_secrets_publisher.publish(event)
        return corr_id

    async def publish_project_ready(
        self,
        project_id: UUID,
        deployment_config_id: UUID | None,
        auto_deploy: bool,
        correlation_id: UUID,
    ) -> None:
        event = ProjectReadyEvent(
            project_id=str(project_id),
            deployment_config_id=str(deployment_config_id) if deployment_config_id else None,
            auto_deploy=auto_deploy,
            correlation_id=str(correlation_id),
            timestamp=datetime.now(UTC).isoformat(),
        )

        logger.info(f'Publishing project.ready for project {project_id}')
        await self._project_ready_publisher.publish(event)

    async def publish_project_failed(
        self,
        project_id: UUID,
        failed_step: str,
        error_message: str,
        correlation_id: UUID,
    ) -> None:
        event = ProjectFailedEvent(
            project_id=str(project_id),
            failed_step=failed_step,
            error_message=error_message,
            correlation_id=str(correlation_id),
            timestamp=datetime.now(UTC).isoformat(),
        )

        logger.warning(f'Publishing project.failed for project {project_id}: {failed_step} - {error_message}')
        await self._project_failed_publisher.publish(event)

    async def publish_project_deleted(
        self,
        project_id: UUID,
        correlation_id: UUID,
    ) -> None:
        event = {
            'project_id': str(project_id),
            'correlation_id': str(correlation_id),
            'timestamp': datetime.now(UTC).isoformat(),
        }

        logger.info(f'Publishing project.deleted for project {project_id}')
        await self._project_deleted_publisher.publish(event)

        await self._logs_publisher.publish({
            "service": "project-service",
            "level": "INFO",
            "message": f"Project deleted: {project_id}",
            "project_id": str(project_id),
            "action": "project.deleted",
            "timestamp": datetime.now(UTC).isoformat(),
            "environment": "development"
        })
