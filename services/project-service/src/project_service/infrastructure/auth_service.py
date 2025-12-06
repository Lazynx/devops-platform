import logging
from uuid import UUID

import httpx

from project_service.application.interfaces.auth_service import IAuthService

logger = logging.getLogger(__name__)


class AuthServiceImpl(IAuthService):
    def __init__(self, client: httpx.AsyncClient, auth_url: str) -> None:
        self._client = client
        self._auth_url = auth_url

    async def get_current_user_id(self, user_access_token: str) -> UUID:
        headers = {
            'Authorization': f'Bearer {user_access_token}',
            'Content-Type': 'application/json',
        }

        try:
            response = await self._client.get(
                url=self._auth_url + '/api/v1/auth/me',
                headers=headers,
            )
            response.raise_for_status()

            data = response.json()
            user_id = data.get('id')

            if not user_id:
                raise ValueError('User ID not found in response')

            logger.info('Successfully retrieved user ID from auth-service')
            return UUID(user_id)

        except httpx.HTTPStatusError as e:
            logger.error(
                f'Auth service error: {e.response.status_code} - {e.response.text}'
            )
            raise
        except Exception as e:
            logger.error(f'Unexpected error calling auth-service: {e}')
            raise

    async def get_github_token(self, user_access_token: str) -> str:
        headers = {
            'Authorization': f'Bearer {user_access_token}',
            'Content-Type': 'application/json',
        }

        try:
            response = await self._client.get(
                url=self._auth_url + '/api/v1/auth/oauth/github/token',
                headers=headers,
            )
            response.raise_for_status()

            data = response.json()
            github_token = data.get('github_token')

            if not github_token:
                raise ValueError('GitHub token not found in response')

            logger.info('Successfully retrieved GitHub token from auth-service')
            return github_token

        except httpx.HTTPStatusError as e:
            logger.error(
                f'Auth service error: {e.response.status_code} - {e.response.text}'
            )
            raise
        except Exception as e:
            logger.error(f'Unexpected error calling auth-service: {e}')
            raise
