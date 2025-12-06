import logging

import uvicorn
from dishka import make_async_container
from dishka.integrations import fastapi as fastapi_integration
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from faststream.kafka import KafkaBroker
from faststream.kafka.fastapi import KafkaRouter

from project_service.config import Settings, settings
from project_service.infrastructure.logging import configure_logging
from project_service.ioc import AppProvider
from project_service.presentation.api.projects import router as project_router
from project_service.presentation.api.repositories import router as repository_router

logger = logging.getLogger(__name__)

configure_logging()


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
        title='Project Service',
        description='Project Service',
        version='1.0.0',
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            'http://localhost:3000',
            'http://127.0.0.1:3000',
        ],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    fastapi_integration.setup_dishka(container, app)
    app.include_router(kafka_router)
    app.include_router(repository_router.router)
    app.include_router(project_router.router)
    return app


if __name__ == '__main__':

    uvicorn.run(
        get_app(),
        host='0.0.0.0',
        port=8001,
        log_level='info',
        reload=True,
    )
