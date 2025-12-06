import logging
from contextlib import asynccontextmanager

import uvicorn
from dishka import make_async_container
from dishka.integrations import fastapi as fastapi_integration
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from observability_service.config import Settings, settings
from observability_service.infrastructure.kafka.broker import broker, set_session_factory
from observability_service.ioc import AppProvider
from observability_service.presentation.api import router

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)

container = make_async_container(AppProvider(), context={Settings: settings})


@asynccontextmanager
async def lifespan(app: FastAPI):
    from observability_service.infrastructure.storage.database import create_engine, create_session_factory

    engine = create_engine(settings.postgres.database_url)
    session_factory = create_session_factory(engine)

    set_session_factory(session_factory)

    await broker.start()
    logger.info('Kafka broker started - listening for logs and metrics')
    yield
    await broker.close()
    logger.info('Kafka broker closed')
    await engine.dispose()


def get_app() -> FastAPI:
    app = FastAPI(
        title='Observability Service',
        description='Centralized logging and metrics collection',
        version='1.0',
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    fastapi_integration.setup_dishka(container, app)

    app.include_router(router.router)
    return app


if __name__ == '__main__':
    uvicorn.run(get_app(), host='0.0.0.0', port=8004, log_level='info', reload=True)
