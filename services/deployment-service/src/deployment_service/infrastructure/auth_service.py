from uuid import UUID

import httpx

from deployment_service.application.interfaces import IAuthService


class AuthServiceHTTPClient(IAuthService):
    def __init__(self, base_url: str):
        self._base_url = base_url.rstrip('/')

    async def get_current_user_id(self, access_token: str) -> UUID:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'{self._base_url}/api/v1/auth/me',
                headers={'Authorization': f'Bearer {access_token}'},
            )
            response.raise_for_status()
            data = response.json()
            return UUID(data['id'])

    async def get_github_token(self, access_token: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'{self._base_url}/api/v1/auth/oauth/github/token',
                headers={'Authorization': f'Bearer {access_token}'},
            )
            response.raise_for_status()
            data = response.json()
            github_token = data.get('github_token')
            if not github_token:
                raise ValueError('GitHub token not found in response')
            return github_token

    async def verify_project_access(self, access_token: str, project_id: UUID) -> bool:
        user_id = await self.get_current_user_id(access_token)
        return True

