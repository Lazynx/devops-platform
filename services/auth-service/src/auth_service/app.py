import logging

import uvicorn
from dishka import make_async_container
from dishka.integrations import fastapi as fastapi_integration
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from faststream.security import SASLPlaintext

from auth_service.config import Settings, settings
from auth_service.infrastructure.logging import configure_logging
from auth_service.ioc import AppProvider
from auth_service.presentation.api.auth import router as auth_router
from faststream.kafka import KafkaBroker
from faststream.kafka.fastapi import KafkaRouter


logger = logging.getLogger(__name__)

configure_logging()

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
    app = FastAPI(
        title='Auth Service',
        description='Auth Service',
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

    @app.on_event("startup")
    async def startup_event():
        from auth_service.infrastructure.logging_producer import publish_health_logs
        import asyncio
        asyncio.create_task(publish_health_logs(kafka_router.broker))

    app.include_router(auth_router.router)
    
    from auth_service.presentation.api.system import router as system_router
    app.include_router(system_router.router)
    return app

if __name__ == '__main__':
    uvicorn.run(
        get_app(),
        host='0.0.0.0',
        port=8000,
        log_level='info',
        reload=True,
    )
