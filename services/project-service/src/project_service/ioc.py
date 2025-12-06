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
from project_service.application.interactors.get_user_repositories import (
    GetUserRepositoriesInteractor,
)
from project_service.application.interfaces.auth_service import IAuthService
from project_service.application.interfaces.github_service import IGitHubService
from project_service.application.interfaces.project_repository import IProjectRepository
from project_service.config import Settings
from project_service.infrastructure.auth_service import AuthServiceImpl
from project_service.infrastructure.github_service import GitHubServiceImpl
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
    def get_event_publisher(self) -> ProjectEventPublisher:
        return ProjectEventPublisher(broker=broker)

    @provide(scope=Scope.REQUEST)
    def get_create_project_interactor(
        self,
        project_repository: IProjectRepository,
        auth_service: IAuthService,
        github_service: IGitHubService,
        event_publisher: ProjectEventPublisher,
        config: Settings,
    ) -> CreateProjectInteractor:
        return CreateProjectInteractor(
            project_repository=project_repository,
            auth_service=auth_service,
            github_service=github_service,
            webhook_url=config.webhook_url,
            event_publisher=event_publisher,
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
