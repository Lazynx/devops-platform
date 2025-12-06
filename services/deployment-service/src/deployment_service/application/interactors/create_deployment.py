from datetime import UTC, datetime
from uuid import uuid4

from deployment_service.application.dtos import CreateDeploymentInputDTO, CreateDeploymentOutputDTO
from deployment_service.application.interfaces import (
    IAuthService,
    IDeploymentConfigRepository,
    IDeploymentRepository,
)
from deployment_service.domain.entities import Deployment, DeploymentStatus


class ConfigNotFoundError(Exception):
    def __init__(self, config_id: str):
        super().__init__(f'Deployment config {config_id} not found')


class CreateDeploymentInteractor:
    def __init__(
        self,
        deployment_repo: IDeploymentRepository,
        deployment_config_repo: IDeploymentConfigRepository,
        auth_service: IAuthService,
    ):
        self._deployment_repo = deployment_repo
        self._config_repo = deployment_config_repo
        self._auth_service = auth_service

    async def __call__(self, dto: CreateDeploymentInputDTO) -> CreateDeploymentOutputDTO:
        config = await self._config_repo.get_by_id(dto.config_id)

        if not config:
            raise ConfigNotFoundError(str(dto.config_id))

        await self._auth_service.verify_project_access(dto.user_access_token, config.project_id)

        now = datetime.now(UTC)

        deployment = Deployment(
            id=uuid4(),
            config_id=config.id,
            project_id=config.project_id,
            version=dto.version,
            commit_sha=dto.commit_sha,
            status=DeploymentStatus.PENDING,
            created_at=now,
            updated_at=now,
        )

        saved_deployment = await self._deployment_repo.save(deployment)

        return CreateDeploymentOutputDTO(
            id=saved_deployment.id,
            config_id=saved_deployment.config_id,
            project_id=saved_deployment.project_id,
            version=saved_deployment.version,
            commit_sha=saved_deployment.commit_sha,
            status=saved_deployment.status.value,
            created_at=saved_deployment.created_at,
        )
