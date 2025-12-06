import logging

import uvicorn
from dishka import make_async_container
from dishka.integrations import fastapi as fastapi_integration
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from faststream.kafka import KafkaBroker
from faststream.kafka.fastapi import KafkaRouter

from secrets_service.config import Settings, settings
from secrets_service.infrastructure.logging import setup_logging
from secrets_service.ioc import AppProvider
from secrets_service.presentation.api.router import router as secret_router

logger = logging.getLogger(__name__)

setup_logging()
container = make_async_container(AppProvider(), context={Settings: settings})


def get_app() -> FastAPI:
    kafka_router = KafkaRouter(settings.kafka.bootstrap_servers)

    container = make_async_container(
        AppProvider(),
        context={
            Settings: settings,
            KafkaBroker: kafka_router.broker,
        }
    )

    app = FastAPI(
        title='Secrets Service',
        description='Secrets Management Service with Vault',
        version='1.0',
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    fastapi_integration.setup_dishka(container, app)

    app.include_router(kafka_router)
    app.include_router(secret_router)
    return app


if __name__ == '__main__':
    uvicorn.run(
        get_app(),
        host='0.0.0.0',
        port=8003,
        log_level='info',
        reload=True
    )
