import logging
from uuid import UUID

import docker
from docker.errors import BuildError, DockerException
from docker.models.containers import Container

logger = logging.getLogger(__name__)


class DockerClient:
    def __init__(self, base_url: str = 'unix://var/run/docker.sock'):
        self._client = docker.DockerClient(base_url=base_url)

    async def build_image(
        self, repo_path: str, dockerfile_path: str, image_tag: str, build_args: dict[str, str] | None = None
    ) -> str:
        try:
            logger.info(f'Building image {image_tag} from {repo_path}')
            image, build_logs = self._client.images.build(
                path=repo_path, dockerfile=dockerfile_path, tag=image_tag, buildargs=build_args or {}, rm=True
            )

            for log in build_logs:
                if 'stream' in log:
                    logger.info(log['stream'].strip())

            logger.info(f'Image built successfully: {image.id}')
            return str(image.id)

        except BuildError as e:
            logger.error(f'Build failed: {e}')
            raise RuntimeError(f'Docker build failed: {e}') from e
        except DockerException as e:
            logger.error(f'Docker error: {e}')
            raise RuntimeError(f'Docker error: {e}') from e

    async def run_container(
        self,
        image_tag: str,
        container_name: str,
        environment: dict[str, str],
        ports: dict[str, int],
        cpu_limit: float,
        memory_limit: int,
    ) -> str:
        try:
            logger.info(f'Starting container {container_name} from {image_tag}')

            container: Container = self._client.containers.run(
                image=image_tag,
                name=container_name,
                environment=environment,
                ports=ports,
                detach=True,
                cpu_period=100000,
                cpu_quota=int(cpu_limit * 100000),
                mem_limit=f'{memory_limit}m',
                restart_policy={'Name': 'unless-stopped'},
            )

            logger.info(f'Container started: {container.id}')
            return str(container.id)

        except DockerException as e:
            logger.error(f'Failed to start container: {e}')
            raise RuntimeError(f'Failed to start container: {e}') from e

    async def stop_container(self, container_id: str) -> None:
        try:
            container = self._client.containers.get(container_id)
            container.stop()
            logger.info(f'Container {container_id} stopped')
        except DockerException as e:
            logger.error(f'Failed to stop container: {e}')
            raise RuntimeError(f'Failed to stop container: {e}') from e

    async def remove_container(self, container_id: str) -> None:
        try:
            container = self._client.containers.get(container_id)
            container.remove(force=True)
            logger.info(f'Container {container_id} removed')
        except DockerException as e:
            logger.error(f'Failed to remove container: {e}')
            raise RuntimeError(f'Failed to remove container: {e}') from e

    async def get_container_logs(self, container_id: str, tail: int = 100) -> str:
        try:
            container = self._client.containers.get(container_id)
            logs = container.logs(tail=tail, timestamps=True)
            return logs.decode('utf-8')
        except DockerException as e:
            logger.error(f'Failed to get logs: {e}')
            raise RuntimeError(f'Failed to get logs: {e}') from e

    async def get_container_status(self, container_id: str) -> str:
        try:
            container = self._client.containers.get(container_id)
            return container.status
        except DockerException as e:
            logger.error(f'Failed to get status: {e}')
            raise RuntimeError(f'Failed to get status: {e}') from e
