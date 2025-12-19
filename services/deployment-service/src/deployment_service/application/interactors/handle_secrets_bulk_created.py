import logging
from uuid import UUID, uuid4

from deployment_service.domain.entities import DeploymentConfig, Deployment, DeploymentStatus, Environment
from deployment_service.infrastructure.sqlalchemy.deployment_config_repository import DeploymentConfigRepository
from deployment_service.infrastructure.sqlalchemy.deployment_repository import DeploymentRepository
from deployment_service.infrastructure.nomad.client import NomadClient
from deployment_service.infrastructure.nomad.job_generators import generate_build_job_hcl, generate_deploy_job_hcl
from deployment_service.infrastructure.messaging.publisher import MessagePublisher

logger = logging.getLogger(__name__)

class HandleSecretsBulkCreatedInteractor:
    def __init__(
        self,
        config_repo: DeploymentConfigRepository,
        deployment_repo: DeploymentRepository,
        nomad_client: NomadClient,
        publisher: MessagePublisher,
        registry_url: str,
        repository_name: str,
        nexus_user: str,
        nexus_password: str,
    ):
        self._config_repo = config_repo
        self._deployment_repo = deployment_repo
        self._nomad_client = nomad_client
        self._publisher = publisher
        self._registry_url = registry_url
        self._repository_name = repository_name
        self._nexus_user = nexus_user
        self._nexus_password = nexus_password

    async def execute(
        self,
        project_id: str,
        name: str,
        github_repo_url: str,
        github_token: str,
        start_command: str,
        secrets: list[dict],
        deployment_config_data: dict | None,
        auto_deploy: bool,
        correlation_id: str,
    ) -> None:
        logger.info(f"Handling secrets.bulk_created for project {project_id}")

        # 1. Create DeploymentConfig
        if deployment_config_data:
            env_str = deployment_config_data.get('environment', 'development').lower()
            config = DeploymentConfig(
                id=uuid4(),
                project_id=UUID(project_id) if isinstance(project_id, str) else project_id,
                github_repo_url=github_repo_url or '',
                environment=Environment(env_str),
                instance_count=deployment_config_data.get('instance_count', 1),
                cpu_limit=deployment_config_data.get('cpu_limit', 0.5),
                memory_limit=deployment_config_data.get('memory_limit', 512),
                port=deployment_config_data.get('port', 8000),
                health_check_path=deployment_config_data.get('health_check_path', '/health'),
                dockerfile_path=deployment_config_data.get('dockerfile_path', './Dockerfile'),
                docker_build_context=deployment_config_data.get('docker_build_context', '.'),
                auto_scaling_enabled=deployment_config_data.get('auto_scaling_enabled', False),
                min_instances=deployment_config_data.get('min_instances', 1),
                max_instances=deployment_config_data.get('max_instances', 10),
            )
            self._config_repo._session.add(config)
            await self._config_repo._session.flush()

            auto_deploy = True
            if auto_deploy:
                deployment = Deployment(
                    id=uuid4(),
                    config_id=config.id,
                    project_id=UUID(project_id) if isinstance(project_id, str) else project_id,
                    version="v1",
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
                    project_id=project_id,
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
                    return
                
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
                    return
                
                logger.info(f"Build job {build_job_id} completed successfully. Starting deployment...")

                deployment.mark_deploying()
                await self._deployment_repo._session.commit()
                await self._publisher.publish_deployment_deploying(
                    deployment_id=deployment.id,
                    project_id=deployment.project_id,
                )
                
                image_url = f"{self._registry_url}/{self._repository_name}/project-{project_id}:{deployment.version}"

                deploy_job_hcl = generate_deploy_job_hcl(
                    deployment_id=str(deployment.id),
                    project_id=project_id,
                    project_name=name,
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
                    return

                image_url = f"{self._registry_url}/{self._repository_name}/project-{project_id}:{deployment.version}"
                deployment_url = f"http://{name}-{str(deployment.id)[:8]}.localhost:8090"
                deployment.mark_running(image_url, deployment_url)
                await self._deployment_repo._session.commit()
                await self._publisher.publish_deployment_running(
                    deployment_id=deployment.id,
                    project_id=deployment.project_id,
                    image_url=image_url,
                    deployment_url=deployment_url,
                )
                
                logger.info(f"Deployment {deployment.id} is now running")


