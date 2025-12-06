from collections.abc import AsyncIterable

from dishka import Provider, Scope, from_context, provide
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

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
from deployment_service.infrastructure.sqlalchemy.database import create_engine, create_session_factory
from deployment_service.infrastructure.sqlalchemy.deployment_config_repository import (
    DeploymentConfigRepository,
)
from deployment_service.infrastructure.sqlalchemy.deployment_repository import DeploymentRepository


class AppProvider(Provider):
    config = from_context(provides=Settings, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def get_engine(self, config: Settings) -> AsyncEngine:
        return create_engine(config.postgres.database_url)

    @provide(scope=Scope.APP)
    def get_session_maker(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return create_session_factory(engine)

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

    deployment_repository = provide(
        DeploymentRepository,
        scope=Scope.REQUEST,
        provides=IDeploymentRepository,
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

    create_deployment_config_interactor = provide(
        CreateDeploymentConfigInteractor,
        scope=Scope.REQUEST,
    )

    create_deployment_interactor = provide(
        CreateDeploymentInteractor,
        scope=Scope.REQUEST,
    )
