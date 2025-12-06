from uuid import UUID

from deployment_service.application.dtos import GetDeploymentOutputDTO
from deployment_service.application.interfaces import IDeploymentRepository


class GetDeploymentInteractor:
    def __init__(self, deployment_repo: IDeploymentRepository):
        self._deployment_repo = deployment_repo

    async def __call__(self, deployment_id: UUID) -> GetDeploymentOutputDTO:
        deployment = await self._deployment_repo.get_by_id(deployment_id)

        if not deployment:
            raise ValueError(f'Deployment {deployment_id} not found')

        return GetDeploymentOutputDTO(
            id=deployment.id,
            config_id=deployment.config_id,
            project_id=deployment.project_id,
            version=deployment.version,
            commit_sha=deployment.commit_sha,
            image_url=deployment.image_url,
            status=deployment.status.value,
            error_message=deployment.error_message,
            deployed_at=deployment.deployed_at,
            stopped_at=deployment.stopped_at,
            created_at=deployment.created_at,
            updated_at=deployment.updated_at,
        )
