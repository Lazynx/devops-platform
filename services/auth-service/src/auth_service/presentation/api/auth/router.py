import logging
from typing import Annotated
from urllib.parse import urlencode

import httpx
from dishka import FromDishka
from dishka.integrations.fastapi import inject
from faststream.kafka import KafkaBroker
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth_service.application.dtos import (
    GetGitHubTokenInputDTO,
    GetUserInputDTO,
    LogoutInputDTO,
    OAuthCallbackInputDTO,
    RefreshTokenInputDTO,
)
from auth_service.application.interactors.get_github_token import GetGitHubTokenInteractor
from auth_service.application.interactors.get_user import GetUserInteractor
from auth_service.application.interactors.github_oauth_login import GitHubOAuthLoginInteractor
from auth_service.application.interactors.logout import LogoutInteractor
from auth_service.application.interactors.refresh_token import RefreshTokenInteractor
from auth_service.config import settings
from auth_service.infrastructure.oauth.github_oauth_provider import GithubOauthProvider
from auth_service.presentation.api.auth.schemas import (
    GitHubAuthUrlResponse,
    GitHubTokenResponse,
    LogoutResponse,
    RefreshTokenResponse,
    UserResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/api/v1/auth',
    tags=['Authentication'],
)
security = HTTPBearer()


@router.get(
    '/github',
    response_model=GitHubAuthUrlResponse,
    status_code=status.HTTP_200_OK,
    summary='Redirect to GitHub OAuth',
)
@inject
async def github_login(
    github_provider: FromDishka[GithubOauthProvider],
) -> GitHubAuthUrlResponse:
    auth_url = await github_provider.get_authorization_url()
    return GitHubAuthUrlResponse(authorization_url=auth_url)


@router.get('/github/callback', summary='GitHub OAuth callback')
@inject
async def github_callback(
    code: str,
    request: Request,
    interactor: FromDishka[GitHubOAuthLoginInteractor],
    broker: FromDishka[KafkaBroker],
) -> RedirectResponse:
    try:
        input_dto = OAuthCallbackInputDTO(
            code=code,
            device_info=request.headers.get('user-agent'),
            ip_address=request.client.host if request.client else None,
        )

        result_dto = await interactor(input_dto)

        redirect_params = {
            'access_token': result_dto.access_token,
            'expires_in': str(result_dto.expires_in),
        }
        logger.info('GitHub OAuth callback redirect: %s', redirect_params)

        from datetime import UTC, datetime
        publisher = broker.publisher('service-logs')
        await publisher.publish({
            'service': 'auth-service',
            'level': 'INFO',
            'message': 'User logged in via GitHub',
            'action': 'user.login',
            'timestamp': datetime.now(UTC).isoformat(),
            'environment': 'development',
        })

        redirect_url = f'{settings.frontend_url}/auth/callback?{urlencode(redirect_params)}'

        redirect_response = RedirectResponse(
            url=redirect_url,
            status_code=status.HTTP_302_FOUND,
        )

        redirect_response.set_cookie(
            key='refresh_token',
            value=result_dto.refresh_token,
            max_age=30 * 24 * 60 * 60,
            httponly=True,
            secure=True,
            samesite='none',
            path='/',
        )

        return redirect_response

    except httpx.HTTPStatusError as e:
        logger.error(
            'GitHub OAuth HTTP error',
            extra={'status_code': e.response.status_code},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='OAuth provider error',
        ) from e
    except Exception as e:
        logger.error('GitHub OAuth failed: %s', e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='OAuth authentication failed',
        ) from e


@router.post(
    '/logout',
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary='Logout and clear session',
)
@inject
async def logout(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    response: Response,
    interactor: FromDishka[LogoutInteractor],
    broker: FromDishka[KafkaBroker],
) -> LogoutResponse:
    try:
        input_dto = LogoutInputDTO(token=credentials.credentials)
        await interactor(input_dto)

        from datetime import UTC, datetime
        publisher = broker.publisher('service-logs')
        await publisher.publish({
            'service': 'auth-service',
            'level': 'INFO',
            'message': 'User logged out',
            'action': 'user.logout',
            'timestamp': datetime.now(UTC).isoformat(),
            'environment': 'development',
        })

        response.delete_cookie(
            key='refresh_token',
            path='/',
        )

        return LogoutResponse(message='Successfully logged out')
    except ValueError as e:
        logger.error('%s', e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid token',
        ) from e


@router.post(
    '/refresh',
    response_model=RefreshTokenResponse,
    status_code=status.HTTP_200_OK,
    summary='Refresh access token using HttpOnly cookie',
)
@inject
async def refresh_token(
    interactor: FromDishka[RefreshTokenInteractor],
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> RefreshTokenResponse:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Refresh token not found in cookies',
        )

    try:
        input_dto = RefreshTokenInputDTO(refresh_token=refresh_token)
        result_dto = await interactor(input_dto)

        return RefreshTokenResponse.from_dto(result_dto)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e


@router.get(
    '/me',
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary='Get current user',
)
@inject
async def get_me(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    interactor: FromDishka[GetUserInteractor],
) -> UserResponse:
    try:
        input_dto = GetUserInputDTO(token=credentials.credentials)
        result_dto = await interactor(input_dto)
        return UserResponse.from_dto(result_dto)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid authentication credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        ) from e


@router.get(
    '/oauth/github/token',
    response_model=GitHubTokenResponse,
    status_code=status.HTTP_200_OK,
    summary='Get GitHub OAuth token',
)
@inject
async def get_github_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    interactor: FromDishka[GetGitHubTokenInteractor],
) -> GitHubTokenResponse:
    try:
        input_dto = GetGitHubTokenInputDTO(token=credentials.credentials)
        result_dto = await interactor(input_dto)

        return GitHubTokenResponse(github_token=result_dto.github_token)
    except ValueError as e:
        logger.error('Failed to get GitHub token: %s', e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error('Unexpected error getting GitHub token: %s', e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to retrieve GitHub token',
        ) from e
