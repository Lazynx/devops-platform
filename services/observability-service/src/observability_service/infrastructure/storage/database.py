from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


def create_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url, echo=False, pool_size=20, max_overflow=40)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
