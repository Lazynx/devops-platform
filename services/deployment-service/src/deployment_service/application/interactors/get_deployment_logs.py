from uuid import UUID

from deployment_service.domain.entities import DeploymentStatus
from deployment_service.infrastructure.nomad.client import NomadClient
from deployment_service.infrastructure.sqlalchemy.deployment_repository import DeploymentRepository


class GetDeploymentLogsInteractor:
    def __init__(
        self,
        deployment_repo: DeploymentRepository,
        nomad_client: NomadClient,
    ):
        self._deployment_repo = deployment_repo
        self._nomad_client = nomad_client

    async def __call__(self, deployment_id: UUID, tail: int = 100) -> str:
        deployment = await self._deployment_repo.get_by_id(deployment_id)
        if not deployment:
            raise ValueError(f"Deployment {deployment_id} not found")

        if deployment.status == DeploymentStatus.building:
            job_id = f"build-{deployment.project_id}-{deployment.version}"
            return await self._nomad_client.get_job_logs(job_id, task_name="build", tail=tail)
        elif deployment.status == DeploymentStatus.deploying:
            job_id = f"build-{deployment.project_id}-{deployment.version}"
            build_logs = await self._nomad_client.get_job_logs(job_id, task_name="build", tail=tail)
            return f"[Build completed]\n{build_logs}\n\n[Deploying...]"
        else:
            job_id = f"app-{deployment.project_id}"
            try:
                return await self._nomad_client.get_job_logs(job_id, task_name="app", tail=tail)
            except Exception:
                build_job_id = f"build-{deployment.project_id}-{deployment.version}"
                return await self._nomad_client.get_job_logs(build_job_id, task_name="build", tail=tail)
