import logging
from uuid import UUID

import httpx

from project_service.application.dtos import DeploymentConfigDTO
from project_service.application.exceptions import (
    DeploymentServiceError,
    DeploymentServiceTimeoutError,
)

logger = logging.getLogger(__name__)


class DeploymentServiceClient:
    def __init__(self, client: httpx.AsyncClient, base_url: str, timeout: int = 30):
        self._client = client
        self._base_url = base_url
        self._timeout = timeout

    async def create_deployment_config(
        self,
        user_access_token: str,
        project_id: UUID,
        github_repo_url: str,
        config: DeploymentConfigDTO,
    ) -> UUID:
        headers = {
            'Authorization': f'Bearer {user_access_token}',
            'Content-Type': 'application/json',
        }

        payload = {
            'project_id': str(project_id),
            'github_repo_url': github_repo_url,
            'environment': config.environment,
            'instance_count': config.instance_count,
            'cpu_limit': config.cpu_limit,
            'memory_limit': config.memory_limit,
            'port': config.port,
            'health_check_path': config.health_check_path,
            'dockerfile_path': config.dockerfile_path,
            'docker_build_context': config.docker_build_context,
            'auto_scaling_enabled': config.auto_scaling_enabled,
            'min_instances': config.min_instances,
            'max_instances': config.max_instances,
        }

        logger.debug(f'Calling deployment-service: POST /configs for project {project_id}')

        try:
            response = await self._client.post(
                url=f'{self._base_url}/api/v1/deployments/configs',
                headers=headers,
                json=payload,
                timeout=self._timeout,
            )
            response.raise_for_status()

            data = response.json()
            config_id = data.get('config_id') or data.get('id')

            if not config_id:
                raise DeploymentServiceError('Config ID not found in response')

            logger.info(f'Deployment config created for project {project_id}: {config_id}')
            return UUID(config_id)

        except httpx.TimeoutException as e:
            logger.error(f'Deployment service timeout for project {project_id}')
            raise DeploymentServiceTimeoutError(f'Timeout calling deployment-service: {e}') from e

        except httpx.HTTPStatusError as e:
            logger.error(f'Deployment service call failed: {e.response.status_code} - {e.response.text}')
            raise DeploymentServiceError(
                message=f'Deployment service error: {e.response.text}',
                status_code=e.response.status_code,
            ) from e

        except Exception as e:
            logger.error(f'Unexpected error calling deployment-service: {e}')
            raise DeploymentServiceError(message=str(e)) from e
