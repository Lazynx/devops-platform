import logging
from uuid import UUID

from deployment_service.application.interfaces import (
    IDeploymentConfigRepository,
    IDeploymentRepository,
)
from deployment_service.infrastructure.nomad.client import NomadClient

logger = logging.getLogger(__name__)


class HandleProjectDeletedInteractor:
    def __init__(
        self,
        deployment_repo: IDeploymentRepository,
        config_repo: IDeploymentConfigRepository,
        nomad_client: NomadClient,
    ):
        self._deployment_repo = deployment_repo
        self._config_repo = config_repo
        self._nomad_client = nomad_client

    async def execute(self, project_id: str, correlation_id: str) -> None:
        logger.info(f"Handling project.deleted for project {project_id}")
        project_uuid = UUID(project_id)

        # 1. Stop app job
        await self._nomad_client.stop_job(f"app-{project_id}")

        # 2. Get all configs
        configs = await self._config_repo.get_by_project_id(project_uuid)
        
        for config in configs:
            # 3. Get all deployments for config to stop build jobs
            deployments = await self._deployment_repo.get_by_config_id(config.id)
            for deployment in deployments:
                await self._nomad_client.stop_job(f"build-{project_id}-{deployment.version}")
            
            # 4. Delete deployments
            await self._deployment_repo.delete_by_config_id(config.id)

        # 5. Delete configs
        await self._config_repo.delete_by_project_id(project_uuid)
        
        await self._config_repo._session.commit()
        logger.info(f"Successfully deleted resources for project {project_id}")
