import logging

import uvicorn
from dishka import make_async_container
from dishka.integrations import fastapi as fastapi_integration
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth_service.config import Settings, settings
from auth_service.infrastructure.logging import configure_logging
from auth_service.infrastructure.persistence.sqlalchemy import mapper_registry
from auth_service.ioc import AppProvider
from auth_service.presentation.api.auth import router as auth_router

logger = logging.getLogger(__name__)

configure_logging()
container = make_async_container(AppProvider(), context={Settings: settings})

def get_app() -> FastAPI:
    app = FastAPI(
        title='Auth Service',
        description='Auth Service',
        version='1.0',
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    fastapi_integration.setup_dishka(container, app)

    app.include_router(auth_router.router)
    return app

if __name__ == '__main__':
    uvicorn.run(
        get_app(),
        host='0.0.0.0',
        port=8000,
        log_level='info',
        reload=True,
    )
