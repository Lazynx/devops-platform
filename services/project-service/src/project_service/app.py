import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from dishka import make_async_container
from dishka.integrations import fastapi as fastapi_integration
from dishka.integrations import faststream as faststream_integration
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from faststream.kafka import KafkaBroker
from faststream.kafka.fastapi import KafkaRouter
from prometheus_fastapi_instrumentator import Instrumentator

from project_service.config import Settings, settings
from project_service.infrastructure.logging import configure_logging
from project_service.infrastructure.messaging.consumers import router as consumer_router
from project_service.ioc import AppProvider
from project_service.presentation.api.projects import router as project_router
from project_service.presentation.api.repositories import router as repository_router

logger = logging.getLogger(__name__)

configure_logging()


def get_app() -> FastAPI:
    kafka_router = KafkaRouter(settings.kafka.bootstrap_servers)
    kafka_router.include_router(consumer_router)

    container = make_async_container(
        AppProvider(),
        context={
            Settings: settings,
            KafkaBroker: kafka_router.broker,
        },
    )

    faststream_integration.setup_dishka(container, kafka_router)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        from project_service.infrastructure.logging_producer import publish_health_logs
        task = asyncio.create_task(publish_health_logs(kafka_router.broker))
        yield
        task.cancel()

    app = FastAPI(
        title='Project Service',
        description='Project Service',
        version='1.0.0',
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r'http://localhost:\d+',
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    fastapi_integration.setup_dishka(container, app)
    app.include_router(kafka_router)
    app.include_router(repository_router.router)
    app.include_router(project_router.router)

    from project_service.presentation.api.system import router as system_router
    app.include_router(system_router.router)

    Instrumentator().instrument(app).expose(app, endpoint='/metrics')

    return app


if __name__ == '__main__':
    uvicorn.run(
        'project_service.app:get_app',
        factory=True,
        host='0.0.0.0',
        port=8001,
        log_level='info',
    )
