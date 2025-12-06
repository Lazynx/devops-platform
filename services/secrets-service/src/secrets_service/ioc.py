from collections.abc import AsyncIterable

from dishka import Provider, Scope, from_context, provide
from faststream.kafka import KafkaBroker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from secrets_service.application.interactors.create_secret import CreateSecretInteractor
from secrets_service.application.interactors.delete_secret import DeleteSecretInteractor
from secrets_service.application.interactors.get_secrets import (
    GetSecretsByDeploymentInteractor,
    GetSecretsByProjectInteractor,
    GetSecretValueInteractor,
)
from secrets_service.application.interactors.update_secret import UpdateSecretInteractor
from secrets_service.application.interfaces.secret_repository import SecretRepository
from secrets_service.config import Settings
from secrets_service.infrastructure.messaging.publisher import SecretEventPublisher
from secrets_service.infrastructure.persistence.sqlalchemy.database import new_session_maker
from secrets_service.infrastructure.persistence.sqlalchemy.secret_repository import SqlAlchemySecretRepository
from secrets_service.infrastructure.vault.client import VaultClient


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
    def get_vault_client(self, config: Settings) -> VaultClient:
        return VaultClient(url=config.vault.url, token=config.vault.token.get_secret_value())

    @provide(scope=Scope.APP)
    def get_publisher(self, broker: KafkaBroker) -> SecretEventPublisher:
        return SecretEventPublisher(broker)

    secret_repository = provide(SqlAlchemySecretRepository, scope=Scope.REQUEST, provides=SecretRepository)

    create_secret_interactor = provide(CreateSecretInteractor, scope=Scope.REQUEST)
    get_secrets_by_project_interactor = provide(GetSecretsByProjectInteractor, scope=Scope.REQUEST)
    get_secrets_by_deployment_interactor = provide(GetSecretsByDeploymentInteractor, scope=Scope.REQUEST)
    get_secret_value_interactor = provide(GetSecretValueInteractor, scope=Scope.REQUEST)
    update_secret_interactor = provide(UpdateSecretInteractor, scope=Scope.REQUEST)
    delete_secret_interactor = provide(DeleteSecretInteractor, scope=Scope.REQUEST)
