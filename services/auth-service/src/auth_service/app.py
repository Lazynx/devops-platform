import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from dishka import make_async_container
from dishka.integrations import fastapi as fastapi_integration
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from faststream.kafka import KafkaBroker
from faststream.kafka.fastapi import KafkaRouter
from prometheus_fastapi_instrumentator import Instrumentator

from auth_service.config import Settings, settings
from auth_service.infrastructure.logging import configure_logging
from auth_service.ioc import AppProvider
from auth_service.presentation.api.auth import router as auth_router

logger = logging.getLogger(__name__)

configure_logging()


def get_app() -> FastAPI:
    kafka_router = KafkaRouter(settings.kafka.bootstrap_servers)

    container = make_async_container(
        AppProvider(),
        context={
            Settings: settings,
            KafkaBroker: kafka_router.broker,
        },
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        from auth_service.infrastructure.logging_producer import publish_health_logs
        task = asyncio.create_task(publish_health_logs(kafka_router.broker))
        yield
        task.cancel()

    app = FastAPI(
        title='Auth Service',
        description='Auth Service',
        version='1.0',
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
    app.include_router(auth_router.router)

    from auth_service.presentation.api.system import router as system_router
    app.include_router(system_router.router)

    Instrumentator().instrument(app).expose(app, endpoint='/metrics')

    return app


if __name__ == '__main__':
    uvicorn.run(
        'auth_service.app:get_app',
        factory=True,
        host='0.0.0.0',
        port=8000,
        log_level='info',
    )
