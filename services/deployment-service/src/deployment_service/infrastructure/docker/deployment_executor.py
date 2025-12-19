import logging
from uuid import UUID

import httpx

from deployment_service.application.interfaces import IDeploymentConfigRepository, IDeploymentRepository
from deployment_service.application.interfaces.deployment_executor import DeploymentExecutor
from deployment_service.domain.entities import DeploymentStatus
from deployment_service.infrastructure.docker.client import DockerClient
from deployment_service.infrastructure.github.client import GitHubClient

logger = logging.getLogger(__name__)


class DockerDeploymentExecutor(DeploymentExecutor):
    def __init__(
        self,
        deployment_repo: IDeploymentRepository,
        config_repo: IDeploymentConfigRepository,
        docker_client: DockerClient,
        github_client: GitHubClient,
        secrets_service_url: str,
    ):
        self._deployment_repo = deployment_repo
        self._config_repo = config_repo
        self._docker_client = docker_client
        self._github_client = github_client
        self._secrets_service_url = secrets_service_url

    async def execute_deployment(self, deployment_id: UUID) -> None:
        deployment = await self._deployment_repo.get_by_id(deployment_id)
        if not deployment:
            raise ValueError(f'Deployment {deployment_id} not found')

        config = await self._config_repo.get_by_id(deployment.config_id)
        if not config:
            raise ValueError(f'Config {deployment.config_id} not found')

        try:
            deployment.mark_deploying()
            await self._deployment_repo.save(deployment)

            logger.info(f'Starting deployment {deployment_id}')

            secrets = await self._fetch_secrets(deployment_id)

            env_variables = dict(secrets)

            repo_path = await self._github_client.clone_repository(
                repo_url=config.github_repo_url,
                project_id=str(deployment.project_id),
                commit_sha=deployment.commit_sha,
            )

            image_tag = f'devplatform/{deployment.project_id}:{deployment.version}'

            await self._docker_client.build_image(
                repo_path=repo_path,
                dockerfile_path=config.dockerfile_path,
                image_tag=image_tag,
                build_args=None,
            )

            container_name = f'deployment-{deployment_id}'

            ports = {f'{config.port}/tcp': config.port}

            container_id = await self._docker_client.run_container(
                image_tag=image_tag,
                container_name=container_name,
                environment=env_variables,
                ports=ports,
                cpu_limit=config.cpu_limit,
                memory_limit=config.memory_limit,
            )

            deployment.mark_running(image_url=image_tag)
            await self._deployment_repo.save(deployment)

            logger.info(f'Deployment {deployment_id} completed successfully')

        except Exception as e:
            logger.error(f'Deployment {deployment_id} failed: {e}')
            deployment.mark_failed(str(e))
            await self._deployment_repo.save(deployment)
            raise

    async def stop_deployment(self, deployment_id: UUID) -> None:
        deployment = await self._deployment_repo.get_by_id(deployment_id)
        if not deployment:
            raise ValueError(f'Deployment {deployment_id} not found')

        if deployment.status != DeploymentStatus.running:
            raise ValueError(f'Deployment {deployment_id} is not running')

        try:
            container_name = f'deployment-{deployment_id}'
            await self._docker_client.stop_container(container_name)
            await self._docker_client.remove_container(container_name)

            deployment.mark_stopped()
            await self._deployment_repo.save(deployment)

            logger.info(f'Deployment {deployment_id} stopped')

        except Exception as e:
            logger.error(f'Failed to stop deployment {deployment_id}: {e}')
            raise

    async def get_deployment_logs(self, deployment_id: UUID, tail: int = 100) -> str:
        deployment = await self._deployment_repo.get_by_id(deployment_id)
        if not deployment:
            raise ValueError(f'Deployment {deployment_id} not found')

        container_name = f'deployment-{deployment_id}'
        return await self._docker_client.get_container_logs(container_name, tail)

    async def _fetch_secrets(self, deployment_id: UUID) -> dict[str, str]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f'{self._secrets_service_url}/api/v1/secrets/deployment/{deployment_id}'
                )
                response.raise_for_status()
                secrets_data = response.json()

                return {secret['key']: secret['value'] for secret in secrets_data}

        except httpx.HTTPError as e:
            logger.warning(f'Failed to fetch secrets for deployment {deployment_id}: {e}')
            return {}
