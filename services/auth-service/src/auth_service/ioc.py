from collections.abc import AsyncIterable

from dishka import AnyOf, Provider, Scope, from_context, provide
from faststream.kafka import KafkaBroker
from redis.asyncio import Redis, from_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from auth_service.application.interactors.get_github_token import GetGitHubTokenInteractor
from auth_service.application.interactors.get_user import GetUserInteractor
from auth_service.application.interactors.github_oauth_login import GitHubOAuthLoginInteractor
from auth_service.application.interactors.logout import LogoutInteractor
from auth_service.application.interactors.refresh_token import RefreshTokenInteractor
from auth_service.application.interfaces import (
    IOAuthConnectionRepository,
    ISessionRepository,
    IUserRepository,
)
from auth_service.config import Settings
from auth_service.infrastructure.oauth.github_oauth_provider import GithubOauthProvider
from auth_service.infrastructure.redis.session_repository import RedisSessionRepository
from auth_service.infrastructure.security.jwt_service import JWTService
from auth_service.infrastructure.persistence.sqlalchemy.database import new_session_maker
from auth_service.infrastructure.persistence.sqlalchemy.oauth_connection_repository import (
    SQLAlchemyOAuthConnectionRepository,
)
from auth_service.infrastructure.persistence.sqlalchemy.user_repository import SQLAlchemyUserRepository


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
    async def get_redis(self, config: Settings) -> AsyncIterable[Redis]:
        redis = await from_url(config.redis.url, encoding='utf-8', decode_responses=True)
        yield redis
        await redis.aclose()

    user_repository = provide(
        SQLAlchemyUserRepository,
        scope=Scope.REQUEST,
        provides=AnyOf[SQLAlchemyUserRepository, IUserRepository],
    )

    session_repository = provide(
        RedisSessionRepository,
        scope=Scope.REQUEST,
        provides=ISessionRepository,
    )

    oauth_connection_repository = provide(
        SQLAlchemyOAuthConnectionRepository,
        scope=Scope.REQUEST,
        provides=IOAuthConnectionRepository,
    )

    @provide(scope=Scope.APP)
    def get_jwt_service(self, config: Settings) -> JWTService:
        return JWTService(
            secret_key=config.jwt.secret_key,
            algorithm=config.jwt.algorithm,
            access_token_expire_minutes=config.jwt.access_token_expire_minutes,
            refresh_token_expire_days=config.jwt.refresh_token_expire_days,
        )

    @provide(scope=Scope.APP)
    def get_github_oauth_provider(self, config: Settings) -> GithubOauthProvider:
        return GithubOauthProvider(
            client_id=config.github_oauth.client_id,
            client_secret=config.github_oauth.client_secret,
            redirect_uri=config.github_oauth.redirect_uri,
        )

    @provide(scope=Scope.REQUEST)
    def get_user_interactor(
        self,
        jwt_service: JWTService,
        user_repository: IUserRepository,
        session_repository: ISessionRepository,
    ) -> GetUserInteractor:
        return GetUserInteractor(
            jwt_service=jwt_service,
            user_repository=user_repository,
            session_repository=session_repository,
        )

    github_login_interactor = provide(
        GitHubOAuthLoginInteractor,
        scope=Scope.REQUEST,
    )

    refresh_token_interactor = provide(
        RefreshTokenInteractor,
        scope=Scope.REQUEST,
    )

    logout_interactor = provide(
        LogoutInteractor,
        scope=Scope.REQUEST,
    )

    get_github_token_interactor = provide(
        GetGitHubTokenInteractor,
        scope=Scope.REQUEST,
    )
