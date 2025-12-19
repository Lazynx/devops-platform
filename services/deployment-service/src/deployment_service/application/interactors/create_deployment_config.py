from datetime import UTC, datetime
from uuid import uuid4, UUID

from deployment_service.application.dtos import (
    CreateDeploymentConfigInputDTO,
    CreateDeploymentConfigOutputDTO,
)
from deployment_service.application.interfaces import IAuthService, IDeploymentConfigRepository
from deployment_service.domain.entities import DeploymentConfig, Environment


class ConfigAlreadyExistsError(Exception):
    def __init__(self, project_id: str, environment: str):
        super().__init__(f'Config for project {project_id} in {environment} already exists')


class InvalidResourceLimitsError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class CreateDeploymentConfigInteractor:
    def __init__(
        self,
        deployment_config_repo: IDeploymentConfigRepository,
        auth_service: IAuthService,
    ):
        self._config_repo = deployment_config_repo
        self._auth_service = auth_service

    async def __call__(self, dto: CreateDeploymentConfigInputDTO) -> CreateDeploymentConfigOutputDTO:
        await self._auth_service.verify_project_access(dto.user_access_token, dto.project_id)

        existing = await self._config_repo.get_by_project_and_environment(
            dto.project_id, dto.environment
        )

        if existing:
            raise ConfigAlreadyExistsError(str(dto.project_id), dto.environment)

        self._validate_resources(dto)

        now = datetime.now(UTC)

        config = DeploymentConfig(
            id=uuid4(),
            project_id=dto.project_id,
            github_repo_url=dto.github_repo_url,
            environment=Environment(dto.environment.lower()),
            instance_count=dto.instance_count,
            cpu_limit=dto.cpu_limit,
            memory_limit=dto.memory_limit,
            auto_scaling_enabled=dto.auto_scaling_enabled,
            min_instances=dto.min_instances,
            max_instances=dto.max_instances,
            port=dto.port,
            health_check_path=dto.health_check_path,
            dockerfile_path=dto.dockerfile_path,
            docker_build_context=dto.docker_build_context,
            created_at=now,
            updated_at=now,
        )

        saved_config = await self._config_repo.save(config)

        return CreateDeploymentConfigOutputDTO(
            id=saved_config.id,
            project_id=UUID(str(saved_config.project_id)), # Ensure UUID
            github_repo_url=saved_config.github_repo_url,
            environment=saved_config.environment.value,
            instance_count=saved_config.instance_count,
            cpu_limit=saved_config.cpu_limit,
            memory_limit=saved_config.memory_limit,
            auto_scaling_enabled=saved_config.auto_scaling_enabled,
            min_instances=saved_config.min_instances,
            max_instances=saved_config.max_instances,
            port=saved_config.port,
            health_check_path=saved_config.health_check_path,
            dockerfile_path=saved_config.dockerfile_path,
            docker_build_context=saved_config.docker_build_context,
            created_at=saved_config.created_at,
            updated_at=saved_config.updated_at,
        )

    def _validate_resources(self, dto: CreateDeploymentConfigInputDTO) -> None:
        if dto.instance_count < 1 or dto.instance_count > 20:
            raise InvalidResourceLimitsError('instance_count must be between 1 and 20')

        if dto.cpu_limit < 0.1 or dto.cpu_limit > 16.0:
            raise InvalidResourceLimitsError('cpu_limit must be between 0.1 and 16.0')

        if dto.memory_limit < 128 or dto.memory_limit > 32768:
            raise InvalidResourceLimitsError('memory_limit must be between 128MB and 32GB')

        if dto.auto_scaling_enabled:
            if dto.min_instances >= dto.max_instances:
                raise InvalidResourceLimitsError('min_instances must be less than max_instances')

            if dto.min_instances < 1:
                raise InvalidResourceLimitsError('min_instances must be at least 1')

            if dto.max_instances > 50:
                raise InvalidResourceLimitsError('max_instances cannot exceed 50')
