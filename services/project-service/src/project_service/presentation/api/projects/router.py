from datetime import datetime
from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from project_service.application.exceptions import ProjectNotFoundError
from project_service.application.interactors.create_project import (
    CreateProjectInteractor,
)
from project_service.application.interactors.delete_project import DeleteProjectInteractor
from project_service.application.interactors.get_project_status import GetProjectStatusInteractor
from project_service.application.interactors.get_user_projects import (
    GetUserProjectsInteractor,
)
from project_service.presentation.api.projects.schemas import (
    CreateProjectRequest,
    ErrorResponse,
    ProgressResponse,
    ProjectResponse,
    ProjectStatusResponse,
)

router = APIRouter(
    prefix='/api/v1/projects',
    tags=['Projects'],
)
security = HTTPBearer()


@router.get(
    '/',
    summary='List user projects',
    response_model=list[ProjectResponse],
    status_code=status.HTTP_200_OK,
)
@inject
async def list_projects(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    interactor: FromDishka[GetUserProjectsInteractor],
) -> list[ProjectResponse]:
    projects = await interactor.execute(credentials.credentials)
    return [ProjectResponse.model_validate(p) for p in projects]


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
    input_dto = request.to_input_dto(credentials.credentials)
    response_interactor = await interactor(input_dto)
    return ProjectResponse.model_validate(response_interactor)


@router.get(
    '/{project_id}/status',
    summary='Get project status',
    response_model=ProjectStatusResponse,
    status_code=status.HTTP_200_OK,
)
@inject
async def get_project_status(
    project_id: UUID,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    interactor: FromDishka[GetProjectStatusInteractor],
) -> ProjectStatusResponse:
    try:
        status_dto = await interactor.execute(project_id)

        return ProjectStatusResponse(
            project_id=status_dto.project_id,
            name=status_dto.name,
            status=status_dto.status,
            updated_at=status_dto.updated_at,
            secrets_status=status_dto.secrets_status,
            deployment_status=status_dto.deployment_status,
            deployment_url=status_dto.deployment_url,
            progress=ProgressResponse(
                current_step=status_dto.progress.current_step,
                total_steps=status_dto.progress.total_steps,
                completed_steps=status_dto.progress.completed_steps,
                percentage=status_dto.progress.percentage,
                secrets_count=status_dto.progress.secrets_count,
                deployment_config_id=status_dto.progress.deployment_config_id,
            ),
            error=ErrorResponse(
                step=status_dto.error.step,
                message=status_dto.error.message,
                timestamp=status_dto.error.timestamp,
            ) if status_dto.error else None,
        )
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        ) from None
@router.get(
    '/{project_id}/status/poll',
    summary='Long poll for project status change',
    response_model=ProjectStatusResponse,
    status_code=status.HTTP_200_OK,
)
@inject
async def poll_project_status(
    project_id: UUID,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    interactor: FromDishka[GetProjectStatusInteractor],
    last_updated_at: datetime | None = None,
    timeout: int = 30,
) -> ProjectStatusResponse:
    import asyncio
    from datetime import datetime
    
    max_timeout = min(timeout, 60)
    poll_interval = 2
    elapsed = 0
    
    try:
        while elapsed < max_timeout:
            status_dto = await interactor.execute(project_id)
            
            # If last_updated_at is not provided, return immediately
            # If status_dto.updated_at is newer than last_updated_at, return immediately
            if last_updated_at is None or status_dto.updated_at > last_updated_at:
                return ProjectStatusResponse(
                    project_id=status_dto.project_id,
                    name=status_dto.name,
                    status=status_dto.status,
                    updated_at=status_dto.updated_at,
                    secrets_status=status_dto.secrets_status,
                    deployment_status=status_dto.deployment_status,
                    deployment_url=status_dto.deployment_url,
                    progress=ProgressResponse(
                        current_step=status_dto.progress.current_step,
                        total_steps=status_dto.progress.total_steps,
                        completed_steps=status_dto.progress.completed_steps,
                        percentage=status_dto.progress.percentage,
                        secrets_count=status_dto.progress.secrets_count,
                        deployment_config_id=status_dto.progress.deployment_config_id,
                    ),
                    error=ErrorResponse(
                        step=status_dto.error.step,
                        message=status_dto.error.message,
                        timestamp=status_dto.error.timestamp,
                    ) if status_dto.error else None,
                )
            
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            
        # Timeout reached, return current status
        status_dto = await interactor.execute(project_id)
        return ProjectStatusResponse(
            project_id=status_dto.project_id,
            name=status_dto.name,
            status=status_dto.status,
            updated_at=status_dto.updated_at,
            secrets_status=status_dto.secrets_status,
            deployment_status=status_dto.deployment_status,
            deployment_url=status_dto.deployment_url,
            progress=ProgressResponse(
                current_step=status_dto.progress.current_step,
                total_steps=status_dto.progress.total_steps,
                completed_steps=status_dto.progress.completed_steps,
                percentage=status_dto.progress.percentage,
                secrets_count=status_dto.progress.secrets_count,
                deployment_config_id=status_dto.progress.deployment_config_id,
            ),
            error=ErrorResponse(
                step=status_dto.error.step,
                message=status_dto.error.message,
                timestamp=status_dto.error.timestamp,
            ) if status_dto.error else None,
        )

    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        ) from None
@router.delete(
    '/{project_id}',
    summary='Delete a project',
    status_code=status.HTTP_204_NO_CONTENT,
)
@inject
async def delete_project(
    project_id: UUID,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    interactor: FromDishka[DeleteProjectInteractor],
) -> None:
    try:
        await interactor.execute(project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        ) from None
