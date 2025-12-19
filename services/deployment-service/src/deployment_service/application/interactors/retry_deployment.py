import logging
from uuid import UUID, uuid4

from deployment_service.domain.entities import Deployment, DeploymentStatus
from deployment_service.infrastructure.sqlalchemy.deployment_config_repository import DeploymentConfigRepository
from deployment_service.infrastructure.sqlalchemy.deployment_repository import DeploymentRepository
from deployment_service.infrastructure.nomad.client import NomadClient
from deployment_service.infrastructure.nomad.job_generators import generate_build_job_hcl, generate_deploy_job_hcl
from deployment_service.infrastructure.messaging.publisher import MessagePublisher
from deployment_service.application.interfaces import IAuthService

logger = logging.getLogger(__name__)


class RetryDeploymentInteractor:
    def __init__(
        self,
        config_repo: DeploymentConfigRepository,
        deployment_repo: DeploymentRepository,
        nomad_client: NomadClient,
        publisher: MessagePublisher,
        auth_service: IAuthService,
        registry_url: str,
        repository_name: str,
        nexus_user: str,
        nexus_password: str,
    ):
        self._config_repo = config_repo
        self._deployment_repo = deployment_repo
        self._nomad_client = nomad_client
        self._publisher = publisher
        self._auth_service = auth_service
        self._registry_url = registry_url
        self._repository_name = repository_name
        self._nexus_user = nexus_user
        self._nexus_password = nexus_password

    async def execute(
        self,
        project_id: UUID,
        user_access_token: str,
        start_command: str,
        project_name: str,
    ) -> Deployment:
        logger.info(f"Retrying deployment for project {project_id}")

        github_token = await self._auth_service.get_github_token(user_access_token)

        configs = await self._config_repo.get_by_project_id(project_id)
        if not configs:
            raise ValueError(f"Deployment config for project {project_id} not found")
        config = configs[0]

        existing_deployments = await self._deployment_repo.get_by_project_id(project_id)
        version = f"v{len(existing_deployments) + 1}"

        deployment = Deployment(
            id=uuid4(),
            config_id=config.id,
            project_id=project_id,
            version=version,
            status=DeploymentStatus.pending,
        )
        self._deployment_repo._session.add(deployment)
        await self._deployment_repo._session.flush()

        deployment.mark_building()
        await self._deployment_repo._session.commit()
        await self._publisher.publish_deployment_building(
            deployment_id=deployment.id,
            project_id=deployment.project_id,
        )

        build_job_hcl = generate_build_job_hcl(
            project_id=str(project_id),
            version=deployment.version,
            github_repo_url=config.github_repo_url,
            github_token=github_token,
            dockerfile_path=config.dockerfile_path,
            build_context=config.docker_build_context,
            registry_url=self._registry_url,
            nexus_user=self._nexus_user,
            nexus_password=self._nexus_password,
            repository_name=self._repository_name,
        )

        try:
            await self._nomad_client.create_job(build_job_hcl)
        except Exception as e:
            deployment.mark_failed(f"Build job creation failed: {str(e)}")
            await self._deployment_repo._session.commit()
            await self._publisher.publish_deployment_failed(
                deployment_id=deployment.id,
                project_id=deployment.project_id,
                error_message=f"Build job creation failed: {str(e)}",
            )
            raise

        build_job_id = f"build-{project_id}-{deployment.version}"
        logger.info(f"Waiting for build job {build_job_id} to complete...")

        build_success = await self._nomad_client.wait_for_job_completion(build_job_id, timeout=900, interval=10)

        if not build_success:
            logger.error(f"Build job {build_job_id} failed. Aborting deployment.")
            deployment.mark_failed("Docker image build failed")
            await self._deployment_repo._session.commit()
            await self._publisher.publish_deployment_failed(
                deployment_id=deployment.id,
                project_id=deployment.project_id,
                error_message="Docker image build failed",
            )
            raise ValueError("Docker image build failed")

        logger.info(f"Build job {build_job_id} completed successfully. Starting deployment...")

        deployment.mark_deploying()
        await self._deployment_repo._session.commit()
        await self._publisher.publish_deployment_deploying(
            deployment_id=deployment.id,
            project_id=deployment.project_id,
        )

        secrets = []
        image_url = f"{self._registry_url}/{self._repository_name}/project-{project_id}:{deployment.version}"

        deploy_job_hcl = generate_deploy_job_hcl(
            deployment_id=str(deployment.id),
            project_id=str(project_id),
            project_name=project_name,
            version=deployment.version,
            image_url=image_url,
            port=config.port,
            secrets=secrets,
            start_command=start_command,
            nexus_user=self._nexus_user,
            nexus_password=self._nexus_password,
            registry_url=self._registry_url,
        )

        try:
            await self._nomad_client.create_job(deploy_job_hcl)
        except Exception as e:
            deployment.mark_failed(f"Deploy job creation failed: {str(e)}")
            await self._deployment_repo._session.commit()
            await self._publisher.publish_deployment_failed(
                deployment_id=deployment.id,
                project_id=deployment.project_id,
                error_message=f"Deploy job creation failed: {str(e)}",
            )
            raise

        image_url = f"{self._registry_url}/{self._repository_name}/project-{project_id}:{deployment.version}"
        deployment_url = f"http://{project_name}-{str(deployment.id)[:8]}.localhost:8090"
        deployment.mark_running(image_url, deployment_url)
        await self._deployment_repo._session.commit()
        await self._publisher.publish_deployment_running(
            deployment_id=deployment.id,
            project_id=deployment.project_id,
            image_url=image_url,
            deployment_url=deployment_url,
        )

        logger.info(f"Deployment {deployment.id} is now running at {deployment_url}")
        return deployment

