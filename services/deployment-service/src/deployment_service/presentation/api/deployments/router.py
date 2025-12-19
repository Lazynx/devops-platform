import logging
from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from deployment_service.application.dtos import (
    CreateDeploymentConfigInputDTO,
    CreateDeploymentInputDTO,
)
from deployment_service.application.interactors.create_deployment import CreateDeploymentInteractor
from deployment_service.application.interactors.create_deployment_config import (
    CreateDeploymentConfigInteractor,
)
from deployment_service.application.interactors.get_deployment import GetDeploymentInteractor
from deployment_service.application.interactors.get_deployment_logs import GetDeploymentLogsInteractor
from deployment_service.application.interactors.list_deployments import ListDeploymentsInteractor
from deployment_service.application.interactors.stop_deployment import StopDeploymentInteractor
from deployment_service.application.interactors.retry_deployment import RetryDeploymentInteractor
from deployment_service.presentation.api.deployments.schemas import (
    CreateDeploymentConfigRequest,
    CreateDeploymentRequest,
    DeploymentConfigResponse,
    DeploymentDetailResponse,
    DeploymentLogsResponse,
    DeploymentResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/api/v1/deployments',
    tags=['Deployments'],
)
security = HTTPBearer()


class RetryDeploymentRequest(BaseModel):
    start_command: str
    project_name: str


@router.post(
    '/configs',
    response_model=DeploymentConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary='Create deployment configuration',
)
@inject
async def create_deployment_config(
    request: CreateDeploymentConfigRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    interactor: FromDishka[CreateDeploymentConfigInteractor],
) -> DeploymentConfigResponse:
    try:
        input_dto = CreateDeploymentConfigInputDTO(
            user_access_token=credentials.credentials,
            project_id=request.project_id,
            github_repo_url=request.github_repo_url,
            environment=request.environment,
            instance_count=request.instance_count,
            cpu_limit=request.cpu_limit,
            memory_limit=request.memory_limit,
            auto_scaling_enabled=request.auto_scaling_enabled,
            min_instances=request.min_instances,
            max_instances=request.max_instances,
            port=request.port,
            health_check_path=request.health_check_path,
            dockerfile_path=request.dockerfile_path,
            docker_build_context=request.docker_build_context,
        )

        output_dto = await interactor(input_dto)

        return DeploymentConfigResponse(
            id=output_dto.id,
            project_id=output_dto.project_id,
            github_repo_url=output_dto.github_repo_url,
            environment=output_dto.environment,
            instance_count=output_dto.instance_count,
            cpu_limit=output_dto.cpu_limit,
            memory_limit=output_dto.memory_limit,
            auto_scaling_enabled=output_dto.auto_scaling_enabled,
            min_instances=output_dto.min_instances,
            max_instances=output_dto.max_instances,
            port=output_dto.port,
            health_check_path=output_dto.health_check_path,
            dockerfile_path=output_dto.dockerfile_path,
            docker_build_context=output_dto.docker_build_context,
            created_at=output_dto.created_at,
            updated_at=output_dto.updated_at,
        )
    except Exception as e:
        logger.error(f'Failed to create deployment config: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    '/',
    response_model=DeploymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary='Create deployment',
)
@inject
async def create_deployment(
    request: CreateDeploymentRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    interactor: FromDishka[CreateDeploymentInteractor],
) -> DeploymentResponse:
    try:
        input_dto = CreateDeploymentInputDTO(
            user_access_token=credentials.credentials,
            config_id=request.config_id,
            version=request.version,
            commit_sha=request.commit_sha,
        )

        output_dto = await interactor(input_dto)

        return DeploymentResponse(
            id=output_dto.id,
            config_id=output_dto.config_id,
            project_id=output_dto.project_id,
            version=output_dto.version,
            commit_sha=output_dto.commit_sha,
            status=output_dto.status,
            created_at=output_dto.created_at,
        )
    except Exception as e:
        logger.error(f'Failed to create deployment: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    '/{deployment_id}',
    response_model=DeploymentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary='Get deployment details',
)
@inject
async def get_deployment(
    deployment_id: str,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    interactor: FromDishka[GetDeploymentInteractor],
) -> DeploymentDetailResponse:
    try:
        from uuid import UUID

        output_dto = await interactor(UUID(deployment_id))

        return DeploymentDetailResponse(
            id=output_dto.id,
            config_id=output_dto.config_id,
            project_id=output_dto.project_id,
            version=output_dto.version,
            commit_sha=output_dto.commit_sha,
            image_url=output_dto.image_url,
            deployment_url=output_dto.deployment_url,
            status=output_dto.status,
            error_message=output_dto.error_message,
            deployed_at=output_dto.deployed_at,
            stopped_at=output_dto.stopped_at,
            created_at=output_dto.created_at,
            updated_at=output_dto.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f'Failed to get deployment: {e}', exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    '/project/{project_id}',
    response_model=list[DeploymentDetailResponse],
    status_code=status.HTTP_200_OK,
    summary='List project deployments',
)
@inject
async def list_deployments(
    project_id: str,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    interactor: FromDishka[ListDeploymentsInteractor],
) -> list[DeploymentDetailResponse]:
    try:
        from uuid import UUID

        deployments = await interactor(UUID(project_id))

        return [
            DeploymentDetailResponse(
                id=d.id,
                config_id=d.config_id,
                project_id=d.project_id,
                version=d.version,
                commit_sha=d.commit_sha,
                image_url=d.image_url,
                deployment_url=d.deployment_url,
                status=d.status,
                error_message=d.error_message,
                deployed_at=d.deployed_at,
                stopped_at=d.stopped_at,
                created_at=d.created_at,
                updated_at=d.updated_at,
            )
            for d in deployments
        ]
    except Exception as e:
        logger.error(f'Failed to list deployments: {e}', exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    '/{deployment_id}/stop',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Stop deployment',
)
@inject
async def stop_deployment(
    deployment_id: str,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    interactor: FromDishka[StopDeploymentInteractor],
) -> None:
    try:
        from uuid import UUID

        await interactor(UUID(deployment_id))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f'Failed to stop deployment: {e}', exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    '/{deployment_id}/logs',
    response_model=DeploymentLogsResponse,
    status_code=status.HTTP_200_OK,
    summary='Get deployment logs',
)
@inject
async def get_deployment_logs(
    interactor: FromDishka[GetDeploymentLogsInteractor],
    deployment_id: str,
    tail: int = 100,
) -> DeploymentLogsResponse:
    try:
        logs = await interactor(UUID(deployment_id), tail)
        return DeploymentLogsResponse(logs=logs)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f'Failed to get logs: {e}', exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    '/project/{project_id}/retry',
    response_model=DeploymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary='Retry deployment for a project',
)
@inject
async def retry_deployment(
    project_id: str,
    request: RetryDeploymentRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    interactor: FromDishka[RetryDeploymentInteractor],
) -> DeploymentResponse:
    try:
        deployment = await interactor.execute(
            project_id=UUID(project_id),
            user_access_token=credentials.credentials,
            start_command=request.start_command,
            project_name=request.project_name,
        )

        return DeploymentResponse(
            id=deployment.id,
            config_id=deployment.config_id,
            project_id=deployment.project_id,
            version=deployment.version,
            commit_sha=deployment.commit_sha,
            status=deployment.status.value,
            deployment_url=deployment.deployment_url,
            created_at=deployment.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f'Failed to retry deployment: {e}', exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    '/{deployment_id}/status/poll',
    response_model=DeploymentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary='Long poll for deployment status change',
)
@inject
async def poll_deployment_status(
    deployment_id: str,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    interactor: FromDishka[GetDeploymentInteractor],
    last_status: str | None = None,
    timeout: int = 30,
) -> DeploymentDetailResponse:
    import asyncio
    
    max_timeout = min(timeout, 60)
    poll_interval = 2
    elapsed = 0
    
    try:
        while elapsed < max_timeout:
            deployment = await interactor(UUID(deployment_id))
            
            if last_status is None or deployment.status != last_status:
                return DeploymentDetailResponse(
                    id=deployment.id,
                    config_id=deployment.config_id,
                    project_id=deployment.project_id,
                    version=deployment.version,
                    commit_sha=deployment.commit_sha,
                    image_url=deployment.image_url,
                    deployment_url=deployment.deployment_url,
                    status=deployment.status,
                    error_message=deployment.error_message,
                    deployed_at=deployment.deployed_at,
                    stopped_at=deployment.stopped_at,
                    created_at=deployment.created_at,
                    updated_at=deployment.updated_at,
                )
            
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        
        deployment = await interactor(UUID(deployment_id))
        return DeploymentDetailResponse(
            id=deployment.id,
            config_id=deployment.config_id,
            project_id=deployment.project_id,
            version=deployment.version,
            commit_sha=deployment.commit_sha,
            image_url=deployment.image_url,
            deployment_url=deployment.deployment_url,
            status=deployment.status,
            error_message=deployment.error_message,
            deployed_at=deployment.deployed_at,
            stopped_at=deployment.stopped_at,
            created_at=deployment.created_at,
            updated_at=deployment.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f'Failed to poll deployment status: {e}', exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
