import logging

import uvicorn
from dishka import make_async_container
from dishka.integrations import fastapi as fastapi_integration
from dishka.integrations import faststream as faststream_integration
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from faststream import FastStream
from faststream.kafka import KafkaBroker
from faststream.kafka.fastapi import KafkaRouter
from faststream.security import SASLPlaintext

from secrets_service.config import Settings, settings
from secrets_service.infrastructure.logging import setup_logging
from secrets_service.ioc import AppProvider
from secrets_service.infrastructure.messaging.consumers import router as consumer_router
from secrets_service.presentation.api.router import router as secret_router

logger = logging.getLogger(__name__)

setup_logging()

security = SASLPlaintext(
    username=settings.kafka.username,
    password=settings.kafka.password,
)


def get_app() -> FastAPI:
    kafka_router = KafkaRouter(
        settings.kafka.bootstrap_servers,
        security=security,
    )

    container = make_async_container(
        AppProvider(),
        context={
            Settings: settings,
            KafkaBroker: kafka_router.broker,
        }
    )

    faststream_integration.setup_dishka(container, kafka_router)
    kafka_router.include_router(consumer_router)

    app = FastAPI(
        title='Secrets Service',
        description='Secrets Management Service with Vault',
        version='1.0',
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
    app.include_router(secret_router)
    
    from secrets_service.presentation.api.system import router as system_router
    app.include_router(system_router.router)

    @app.on_event("startup")
    async def startup_event():
        from secrets_service.infrastructure.logging_producer import publish_health_logs
        import asyncio
        asyncio.create_task(publish_health_logs(kafka_router.broker))

    return app


if __name__ == '__main__':
    uvicorn.run(
        get_app(),
        host='0.0.0.0',
        port=8003,
        log_level='info',
        reload=True
    )
