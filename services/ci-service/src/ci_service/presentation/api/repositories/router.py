import logging
from dataclasses import asdict
from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ci_service.application.interactors.analyze_repository import AnalyzeRepositoryInteractor
from ci_service.application.interactors.get_user_repositories import (
    GetUserRepositoriesInteractor,
)
from ci_service.presentation.api.repositories.schemas import (
    AnalyzeRepositoryRequest,
    GetRepositoriesResponse,
    GitHubRepositoryResponse,
    RepositoryConfigResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/api/v1/repositories',
    tags=['Repositories'],
)
security = HTTPBearer()


@router.get(
    '/',
    summary='Get user GitHub repositories',
    response_model=GetRepositoriesResponse,
)
@inject
async def get_repositories(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    interactor: FromDishka[GetUserRepositoriesInteractor],
) -> GetRepositoriesResponse:
    response_interactor = await interactor(user_access_token=credentials.credentials)
    return GetRepositoriesResponse(
        repositories=[GitHubRepositoryResponse(**asdict(repo)) for repo in response_interactor]
    )

@router.get(
    '/{owner}/{repo}/config',
    summary='Analyze repository configuration',
    response_model=RepositoryConfigResponse,
)
@inject
async def analyze_repository_config(
    owner: str,
    repo: str,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    interactor: FromDishka[AnalyzeRepositoryInteractor],
    root_directory: str = './',
) -> RepositoryConfigResponse:
    response_interactor = await interactor(AnalyzeRepositoryRequest.to_input_dto(
        owner=owner,
        repo=repo,
        root_directory=root_directory,
        user_access_token=credentials.credentials,
    ))
    return RepositoryConfigResponse(**asdict(response_interactor))
