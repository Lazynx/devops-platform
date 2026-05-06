from collections.abc import AsyncIterable

import httpx
from dishka import Provider, Scope, from_context, provide
from faststream.kafka import KafkaBroker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from project_service.application.interactors.analyze_repository import (
    AnalyzeRepositoryInteractor,
)
from project_service.application.interactors.create_project import (
    CreateProjectInteractor,
)
from project_service.application.interactors.delete_project import DeleteProjectInteractor
from project_service.application.interactors.get_project_status import GetProjectStatusInteractor
from project_service.application.interactors.get_user_projects import (
    GetUserProjectsInteractor,
)
from project_service.application.interactors.get_user_repositories import (
    GetUserRepositoriesInteractor,
)
from project_service.application.interactors.handle_deployment_config_created import (
    HandleDeploymentConfigCreatedInteractor,
)
from project_service.application.interactors.handle_deployment_config_failed import (
    HandleDeploymentConfigFailedInteractor,
)
from project_service.application.interactors.handle_deployment_status_changed import (
    HandleDeploymentStatusChangedInteractor,
)
from project_service.application.interactors.handle_secrets_bulk_created import (
    HandleSecretsBulkCreatedInteractor,
)
from project_service.application.interactors.handle_secrets_failed import (
    HandleSecretsFailedInteractor,
)
from project_service.application.interactors.trigger_deployment_config import TriggerDeploymentConfigInteractor
from project_service.application.interfaces.auth_service import IAuthService
from project_service.application.interfaces.github_service import IGitHubService
from project_service.application.interfaces.project_repository import IProjectRepository
from project_service.config import Settings
from project_service.infrastructure.auth_service import AuthServiceImpl
from project_service.infrastructure.deployment_service import DeploymentServiceClient
from project_service.infrastructure.github_service import GitHubServiceImpl
from project_service.infrastructure.messaging.pending_configs_store import PendingConfigsStore
from project_service.infrastructure.messaging.publisher import ProjectEventPublisher
from project_service.infrastructure.sqlalchemy.database import new_session_maker
from project_service.infrastructure.sqlalchemy.project_repository import (
    SQLAlchemyProjectRepository,
)


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

    @provide(scope=Scope.APP)
    async def get_http_client(self) -> AsyncIterable[httpx.AsyncClient]:
        client = httpx.AsyncClient(
            timeout=10.0,
        )
        yield client
        await client.aclose()

    @provide(scope=Scope.REQUEST)
    def get_github_service(self, http_client: httpx.AsyncClient, config: Settings) -> IGitHubService:
        return GitHubServiceImpl(client=http_client, github_api_url=config.github_api_url)

    @provide(scope=Scope.REQUEST)
    def get_auth_service(self, http_client: httpx.AsyncClient, config: Settings) -> IAuthService:
        return AuthServiceImpl(client=http_client, auth_url=config.auth_service_url)

    @provide(scope=Scope.APP)
    def get_event_publisher(self, broker: KafkaBroker) -> ProjectEventPublisher:
        return ProjectEventPublisher(broker=broker)

    @provide(scope=Scope.APP)
    def get_pending_configs_store(self) -> PendingConfigsStore:
        return PendingConfigsStore()

    @provide(scope=Scope.APP)
    def get_deployment_client(self, http_client: httpx.AsyncClient, config: Settings) -> DeploymentServiceClient:
        return DeploymentServiceClient(
            client=http_client,
            base_url=config.deployment_service_url,
            timeout=config.deployment_config_timeout,
        )

    @provide(scope=Scope.REQUEST)
    def get_handle_secrets_bulk_created_interactor(
        self,
        project_repository: IProjectRepository,
        event_publisher: ProjectEventPublisher,
        deployment_client: DeploymentServiceClient,
        pending_configs_store: PendingConfigsStore,
    ) -> HandleSecretsBulkCreatedInteractor:
        return HandleSecretsBulkCreatedInteractor(
            project_repository=project_repository,
            event_publisher=event_publisher,
            deployment_client=deployment_client,
            pending_configs_store=pending_configs_store,
        )

    @provide(scope=Scope.REQUEST)
    def get_handle_secrets_failed_interactor(
        self,
        project_repository: IProjectRepository,
        event_publisher: ProjectEventPublisher,
        pending_configs_store: PendingConfigsStore,
    ) -> HandleSecretsFailedInteractor:
        return HandleSecretsFailedInteractor(
            project_repository=project_repository,
            event_publisher=event_publisher,
            pending_configs_store=pending_configs_store,
        )

    @provide(scope=Scope.REQUEST)
    def get_handle_deployment_config_created_interactor(
        self,
        project_repository: IProjectRepository,
        event_publisher: ProjectEventPublisher,
    ) -> HandleDeploymentConfigCreatedInteractor:
        return HandleDeploymentConfigCreatedInteractor(
            project_repository=project_repository,
            event_publisher=event_publisher,
        )

    @provide(scope=Scope.REQUEST)
    def get_handle_deployment_config_failed_interactor(
        self,
        project_repository: IProjectRepository,
        event_publisher: ProjectEventPublisher,
    ) -> HandleDeploymentConfigFailedInteractor:
        return HandleDeploymentConfigFailedInteractor(
            project_repository=project_repository,
            event_publisher=event_publisher,
        )

    @provide(scope=Scope.REQUEST)
    def get_handle_deployment_status_changed_interactor(
        self,
        project_repository: IProjectRepository,
    ) -> HandleDeploymentStatusChangedInteractor:
        return HandleDeploymentStatusChangedInteractor(
            project_repository=project_repository,
        )

    @provide(scope=Scope.REQUEST)
    def get_get_user_projects_interactor(
        self,
        project_repository: IProjectRepository,
        auth_service: IAuthService,
    ) -> GetUserProjectsInteractor:
        return GetUserProjectsInteractor(
            project_repository=project_repository,
            auth_service=auth_service,
        )


    @provide(scope=Scope.REQUEST)
    def get_create_project_interactor(
        self,
        project_repository: IProjectRepository,
        auth_service: IAuthService,
        github_service: IGitHubService,
        event_publisher: ProjectEventPublisher,
        pending_configs_store: PendingConfigsStore,
        config: Settings,
    ) -> CreateProjectInteractor:
        return CreateProjectInteractor(
            project_repository=project_repository,
            auth_service=auth_service,
            github_service=github_service,
            webhook_url=config.webhook_url,
            event_publisher=event_publisher,
            pending_configs_store=pending_configs_store,
        )

    @provide(scope=Scope.REQUEST)
    def get_trigger_deployment_config_interactor(
        self,
        project_repository: IProjectRepository,
        deployment_client: DeploymentServiceClient,
        event_publisher: ProjectEventPublisher,
    ) -> TriggerDeploymentConfigInteractor:
        return TriggerDeploymentConfigInteractor(
            repository=project_repository,
            deployment_client=deployment_client,
            publisher=event_publisher,
        )

    project_repository = provide(
        SQLAlchemyProjectRepository,
        scope=Scope.REQUEST,
        provides=IProjectRepository,
    )

    get_user_repositories_interactor = provide(
        GetUserRepositoriesInteractor,
        scope=Scope.REQUEST,
    )

    analyze_repository_interactor = provide(
        AnalyzeRepositoryInteractor,
        scope=Scope.REQUEST,
    )

    get_project_status_interactor = provide(
        GetProjectStatusInteractor,
        scope=Scope.REQUEST,
    )

    delete_project_interactor = provide(
        DeleteProjectInteractor,
        scope=Scope.REQUEST,
    )
