from collections.abc import AsyncIterable

from dishka import Provider, Scope, from_context, provide
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from observability_service.application.interfaces import LogRepository, MetricRepository
from observability_service.config import Settings
from observability_service.infrastructure.storage.database import create_engine, create_session_factory
from observability_service.infrastructure.storage.log_repository import SqlAlchemyLogRepository
from observability_service.infrastructure.storage.metric_repository import SqlAlchemyMetricRepository


class AppProvider(Provider):
    config = from_context(provides=Settings, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def get_engine(self, config: Settings):
        return create_engine(config.postgres.database_url)

    @provide(scope=Scope.APP)
    def get_session_factory(self, engine) -> async_sessionmaker[AsyncSession]:
        return create_session_factory(engine)

    @provide(scope=Scope.REQUEST)
    async def get_session(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> AsyncIterable[AsyncSession]:
        async with session_factory() as session:
            async with session.begin():
                yield session

    log_repository = provide(SqlAlchemyLogRepository, scope=Scope.REQUEST, provides=LogRepository)
    metric_repository = provide(SqlAlchemyMetricRepository, scope=Scope.REQUEST, provides=MetricRepository)
