import logging
from typing import Annotated

import httpx
from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from application.auth_service import AuthService
from domain.schemas import RefreshTokenRequest, TokenPair, UserResponse
from infrastructure.oauth.google_provider import GoogleOAuthProvider
from infrastructure.security.jwt_service import JWTService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/api/v1/auth',
    tags=['Authentication'],
)
security = HTTPBearer()

@router.get('/google', summary='Redirect to Google OAuth')
@inject
async def google_login(
    google_provider: FromDishka[GoogleOAuthProvider],
) -> dict:
    auth_url = await google_provider.get_authorization_url()
    return {'authorization_url': auth_url}


@router.get('/google/callback', summary='Google OAuth callback')
@inject
async def google_callback(
    code: str,
    auth_service: FromDishka[AuthService],
    google_provider: FromDishka[GoogleOAuthProvider],
    request: Request,
) -> TokenPair:
    try:
        access_token = await google_provider.exchange_code(code)
        oauth_user = await google_provider.get_user_info(access_token)
        token_pair, user = await auth_service.authenticate_with_oauth(
            oauth_user=oauth_user,
            device_info=request.headers.get('user-agent'),
            ip_address=request.client.host if request.client else None,
        )

        return token_pair
    except httpx.HTTPStatusError as e:
        error_body = e.response.text
        print(f'HTTP Error: {e.response.status_code} - {error_body}')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'OAuth HTTP error: {e.response.status_code} - {error_body}',
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'OAuth authentication failed: {type(e).__name__}: {str(e)}',
        )

@router.post('/refresh', summary='Refresh access token', response_model=TokenPair)
@inject
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: FromDishka[AuthService],
) -> TokenPair:
    try:
        token_pair, _ = await auth_service.refresh_access_token(request.refresh_token)
        return token_pair
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

@router.post('/logout', summary='Logout (revoke refresh token)')
@inject
async def logout(
    request: RefreshTokenRequest,
    auth_service: FromDishka[AuthService],
) -> dict:
    try:
        await auth_service.logout(request.refresh_token)
        return {'message': 'Successfully logged out'}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get('/me', summary='Get current user', response_model=UserResponse)
@inject
async def get_me(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    jwt_service: FromDishka[JWTService],
    auth_service: FromDishka[AuthService],
) -> UserResponse:
    try:
        token = credentials.credentials
        payload = jwt_service.verify_access_token(token)
        user = await auth_service.get_current_user(payload.sub)
        return user
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid authentication credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )

@router.get('/health', summary='Health check')
async def health_check() -> dict:
    return {'status': 'healthy', 'service': 'auth-service'}
