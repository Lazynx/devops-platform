from collections.abc import AsyncIterable

from dishka import Provider, Scope, from_context, provide
from faststream.kafka import KafkaBroker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from deployment_service.application.interactors.create_deployment import CreateDeploymentInteractor
from deployment_service.application.interactors.create_deployment_config import (
    CreateDeploymentConfigInteractor,
)
from deployment_service.application.interfaces import (
    IAuthService,
    IDeploymentConfigRepository,
    IDeploymentRepository,
)
from deployment_service.application.interfaces.deployment_executor import DeploymentExecutor
from deployment_service.config import Settings
from deployment_service.infrastructure.auth_service import AuthServiceHTTPClient
from deployment_service.infrastructure.docker.client import DockerClient
from deployment_service.infrastructure.docker.deployment_executor import DockerDeploymentExecutor
from deployment_service.infrastructure.github.client import GitHubClient
from deployment_service.infrastructure.sqlalchemy.database import new_session_maker
from deployment_service.application.interactors.handle_secrets_bulk_created import (
    HandleSecretsBulkCreatedInteractor,
)
from deployment_service.application.interactors.get_deployment import (
    GetDeploymentInteractor,
)
from deployment_service.application.interactors.get_deployment_logs import (
    GetDeploymentLogsInteractor,
)
from deployment_service.application.interactors.list_deployments import (
    ListDeploymentsInteractor,
)
from deployment_service.application.interactors.retry_deployment import (
    RetryDeploymentInteractor,
)
from deployment_service.application.interactors.stop_deployment import (
    StopDeploymentInteractor,
)
from deployment_service.application.interactors.handle_project_deleted import (
    HandleProjectDeletedInteractor,
)
from deployment_service.infrastructure.nomad.client import NomadClient
from deployment_service.infrastructure.sqlalchemy.deployment_config_repository import (
    DeploymentConfigRepository,
)
from deployment_service.infrastructure.sqlalchemy.deployment_repository import (
    DeploymentRepository,
)
from deployment_service.infrastructure.messaging.publisher import MessagePublisher


class AppProvider(Provider):
    config = from_context(provides=Settings, scope=Scope.APP)
    broker = from_context(provides=KafkaBroker, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def get_session_maker(self, config: Settings) -> async_sessionmaker[AsyncSession]:
        return new_session_maker(config.postgres)

    @provide(scope=Scope.REQUEST)
    async def get_session(
        self, session_maker: async_sessionmaker[AsyncSession]
    ) -> AsyncIterable[AsyncSession]:
        async with session_maker() as session:
            yield session

    deployment_config_repository = provide(
        DeploymentConfigRepository,
        scope=Scope.REQUEST,
        provides=IDeploymentConfigRepository,
    )
    
    # Also provide the concrete class for injection into interactor
    deployment_config_repository_concrete = provide(
        DeploymentConfigRepository,
        scope=Scope.REQUEST,
    )

    deployment_repository = provide(
        DeploymentRepository,
        scope=Scope.REQUEST,
        provides=IDeploymentRepository,
    )
    
    # Also provide the concrete class for injection into interactor
    deployment_repository_concrete = provide(
        DeploymentRepository,
        scope=Scope.REQUEST,
    )

    @provide(scope=Scope.APP)
    def get_auth_service(self, config: Settings) -> IAuthService:
        return AuthServiceHTTPClient(config.auth_service_url)

    @provide(scope=Scope.APP)
    def get_docker_client(self) -> DockerClient:
        return DockerClient()

    @provide(scope=Scope.APP)
    def get_github_client(self) -> GitHubClient:
        return GitHubClient()
        
    @provide(scope=Scope.APP)
    def get_nomad_client(self, config: Settings) -> NomadClient:
        return NomadClient(config.nomad_url)

    @provide(scope=Scope.REQUEST)
    def get_deployment_executor(
        self,
        deployment_repo: IDeploymentRepository,
        config_repo: IDeploymentConfigRepository,
        docker_client: DockerClient,
        github_client: GitHubClient,
        config: Settings,
    ) -> DeploymentExecutor:
        return DockerDeploymentExecutor(
            deployment_repo=deployment_repo,
            config_repo=config_repo,
            docker_client=docker_client,
            github_client=github_client,
            secrets_service_url=config.secrets_service_url,
        )

    @provide(scope=Scope.REQUEST)
    def get_message_publisher(self, broker: KafkaBroker) -> MessagePublisher:
        return MessagePublisher(broker)

    create_deployment_config_interactor = provide(
        CreateDeploymentConfigInteractor,
        scope=Scope.REQUEST,
    )

    create_deployment_interactor = provide(
        CreateDeploymentInteractor,
        scope=Scope.REQUEST,
    )
    
    @provide(scope=Scope.REQUEST)
    def get_handle_secrets_bulk_created_interactor(
        self,
        config_repo: DeploymentConfigRepository,
        deployment_repo: DeploymentRepository,
        nomad_client: NomadClient,
        publisher: MessagePublisher,
        config: Settings,
    ) -> HandleSecretsBulkCreatedInteractor:
        return HandleSecretsBulkCreatedInteractor(
            config_repo=config_repo,
            deployment_repo=deployment_repo,
            nomad_client=nomad_client,
            publisher=publisher,
            registry_url=config.nexus_registry_url,
            repository_name=config.nexus_docker_repository,
            nexus_user=config.nexus_user,
            nexus_password=config.nexus_password,
        )

    get_deployment_interactor = provide(
        GetDeploymentInteractor,
        scope=Scope.REQUEST,
    )

    @provide(scope=Scope.REQUEST)
    def get_retry_deployment_interactor(
        self,
        config_repo: DeploymentConfigRepository,
        deployment_repo: DeploymentRepository,
        nomad_client: NomadClient,
        publisher: MessagePublisher,
        auth_service: IAuthService,
        config: Settings,
    ) -> RetryDeploymentInteractor:
        return RetryDeploymentInteractor(
            config_repo=config_repo,
            deployment_repo=deployment_repo,
            nomad_client=nomad_client,
            publisher=publisher,
            auth_service=auth_service,
            registry_url=config.nexus_registry_url,
            repository_name=config.nexus_docker_repository,
            nexus_user=config.nexus_user,
            nexus_password=config.nexus_password,
        )

    get_deployment_logs_interactor = provide(
        GetDeploymentLogsInteractor,
        scope=Scope.REQUEST,
    )

    list_deployments_interactor = provide(
        ListDeploymentsInteractor,
        scope=Scope.REQUEST,
    )

    stop_deployment_interactor = provide(
        StopDeploymentInteractor,
        scope=Scope.REQUEST,
    )

    handle_project_deleted_interactor = provide(
        HandleProjectDeletedInteractor,
        scope=Scope.REQUEST,
    )
