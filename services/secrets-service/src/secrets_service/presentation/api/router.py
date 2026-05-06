import logging
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException, status

from secrets_service.application.dtos import CreateBulkSecretsDTO, CreateSecretDTO, SecretItemDTO, UpdateSecretDTO
from secrets_service.application.interactors.create_bulk_secrets import CreateBulkSecretsInteractor
from secrets_service.application.interactors.create_secret import CreateSecretInteractor
from secrets_service.application.interactors.delete_secret import DeleteSecretInteractor
from secrets_service.application.interactors.get_secrets import (
    GetSecretsByDeploymentInteractor,
    GetSecretsByProjectInteractor,
    GetSecretValueInteractor,
)
from secrets_service.application.interactors.update_secret import UpdateSecretInteractor
from secrets_service.presentation.api.schemas import (
    CreateBulkSecretsRequest,
    CreateSecretRequest,
    DeleteSecretResponse,
    SecretResponse,
    SecretWithValueResponse,
    UpdateSecretRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/v1/secrets', tags=['Secrets'])


@router.post('', response_model=SecretResponse, status_code=status.HTTP_201_CREATED)
@inject
async def create_secret(
    request: CreateSecretRequest,
    interactor: FromDishka[CreateSecretInteractor],
) -> SecretResponse:
    try:
        dto = CreateSecretDTO(
            project_id=request.project_id,
            deployment_id=request.deployment_id,
            key=request.key,
            value=request.value,
            secret_type=request.secret_type,
            description=request.description,
        )
        result = await interactor.execute(dto)

        return SecretResponse.from_dto(result)
    except Exception as e:
        logger.error('Failed to create secret: %s', e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.post('/bulk', response_model=list[SecretResponse], status_code=status.HTTP_201_CREATED)
@inject
async def create_bulk_secrets(
    request: CreateBulkSecretsRequest,
    interactor: FromDishka[CreateBulkSecretsInteractor],
) -> list[SecretResponse]:
    try:
        dto = CreateBulkSecretsDTO(
            project_id=request.project_id,
            deployment_id=request.deployment_id,
            secrets=[
                SecretItemDTO(
                    key=secret.key,
                    value=secret.value,
                    secret_type=secret.secret_type,
                    description=secret.description,
                )
                for secret in request.secrets
            ],
        )
        results = await interactor.execute(dto)

        return [SecretResponse.from_dto(result) for result in results]
    except Exception as e:
        logger.error('Failed to create bulk secrets: %s', e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get('/project/{project_id}', response_model=list[SecretResponse])
@inject
async def get_secrets_by_project(
    project_id: UUID, interactor: FromDishka[GetSecretsByProjectInteractor]
) -> list[SecretResponse]:
    try:
        secrets = await interactor.execute(project_id)
        return [SecretResponse.from_dto(s) for s in secrets]
    except Exception as e:
        logger.error('Failed to get secrets: %s', e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get('/deployment/{deployment_id}', response_model=list[SecretWithValueResponse])
@inject
async def get_secrets_by_deployment(
    deployment_id: UUID, interactor: FromDishka[GetSecretsByDeploymentInteractor]
) -> list[SecretWithValueResponse]:
    try:
        secrets = await interactor.execute(deployment_id)
        return [SecretWithValueResponse.from_dto(s) for s in secrets]
    except Exception as e:
        logger.error('Failed to get secrets: %s', e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get('/{secret_id}', response_model=SecretWithValueResponse)
@inject
async def get_secret_value(
    secret_id: UUID, interactor: FromDishka[GetSecretValueInteractor]
) -> SecretWithValueResponse:
    try:
        secret = await interactor.execute(secret_id)
        return SecretWithValueResponse.from_dto(secret)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        logger.error('Failed to get secret: %s', e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.put('/{secret_id}', response_model=SecretResponse)
@inject
async def update_secret(
    secret_id: UUID,
    request: UpdateSecretRequest,
    interactor: FromDishka[UpdateSecretInteractor],
) -> SecretResponse:
    try:
        dto = UpdateSecretDTO(secret_id=secret_id, value=request.value, description=request.description)
        result = await interactor.execute(dto)

        return SecretResponse.from_dto(result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        logger.error('Failed to update secret: %s', e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.delete('/{secret_id}', response_model=DeleteSecretResponse)
@inject
async def delete_secret(
    secret_id: UUID,
    interactor: FromDishka[DeleteSecretInteractor],
) -> DeleteSecretResponse:
    try:
        await interactor.execute(secret_id)

        return DeleteSecretResponse(message='Secret deleted successfully')
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        logger.error('Failed to delete secret: %s', e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
