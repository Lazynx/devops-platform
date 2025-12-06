from uuid import UUID

from auth_service.application.dtos import GetGitHubTokenInputDTO, GetGitHubTokenOutputDTO
from auth_service.application.interfaces import IOAuthConnectionRepository
from auth_service.domain.entities import OAuthProvider
from auth_service.infrastructure.security.jwt_service import JWTService


class GetGitHubTokenInteractor:
    def __init__(
        self,
        oauth_connection_repository: IOAuthConnectionRepository,
        jwt_service: JWTService,
    ):
        self._oauth_repo = oauth_connection_repository
        self._jwt_service = jwt_service

    async def __call__(self, dto: GetGitHubTokenInputDTO) -> GetGitHubTokenOutputDTO:
        payload = self._jwt_service.verify_access_token(dto.token)
        user_id = UUID(payload.sub)

        oauth_connection = await self._oauth_repo.get_by_user_and_provider(
            user_id=user_id,
            provider=OAuthProvider.GITHUB,
        )

        if not oauth_connection:
            raise ValueError('GitHub OAuth connection not found for user')

        return GetGitHubTokenOutputDTO(github_token=str(oauth_connection.access_token))
