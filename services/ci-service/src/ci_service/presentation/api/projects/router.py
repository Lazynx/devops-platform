from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ci_service.application.interactors.create_project import (
    CreateProjectInteractor,
)
from ci_service.presentation.api.projects.schemas import CreateProjectRequest, ProjectResponse

router = APIRouter(
    prefix='/api/v1/projects',
    tags=['Projects'],
)
security = HTTPBearer()


@router.post(
    '/',
    summary='Create a new project',
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_project(
    request: CreateProjectRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    interactor: FromDishka[CreateProjectInteractor],
) -> ProjectResponse:
    response_interactor = await interactor(request.to_input_dto(credentials.credentials))
    return ProjectResponse.model_validate(response_interactor)
