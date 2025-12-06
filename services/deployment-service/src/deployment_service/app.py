import logging
from contextlib import asynccontextmanager

import uvicorn
from dishka import make_async_container
from dishka.integrations import fastapi as fastapi_integration
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from deployment_service.config import Settings, settings
from deployment_service.infrastructure.logging import setup_logging
from deployment_service.infrastructure.messaging.broker import broker
from deployment_service.ioc import AppProvider
from deployment_service.presentation.api.deployments import router as deployments_router

logger = logging.getLogger(__name__)

setup_logging()
container = make_async_container(AppProvider(), context={Settings: settings})


@asynccontextmanager
async def lifespan(app: FastAPI):
    await broker.start()
    logger.info('Kafka broker started')
    yield
    await broker.close()
    logger.info('Kafka broker closed')


def get_app() -> FastAPI:
    app = FastAPI(
        title='Deployment Service',
        description='Deployment Service',
        version='1.0',
        lifespan=lifespan,
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

    app.include_router(deployments_router.router)
    return app


if __name__ == '__main__':
    uvicorn.run(
        get_app(),
        host='0.0.0.0',
        port=8005,
        log_level='info',
        reload=True,
    )
