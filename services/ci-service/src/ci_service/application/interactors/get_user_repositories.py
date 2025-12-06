import logging

from ci_service.application.dtos import GitHubRepositoryDTO
from ci_service.application.interfaces.auth_service import IAuthService
from ci_service.application.interfaces.github_service import IGitHubService

logger = logging.getLogger(__name__)


class GetUserRepositoriesInteractor:
    def __init__(
        self,
        auth_service: IAuthService,
        github_service: IGitHubService,
    ):
        self._auth_service = auth_service
        self._github_service = github_service

    async def __call__(self, user_access_token: str) -> list[GitHubRepositoryDTO]:
        github_token = await self._auth_service.get_github_token(user_access_token)
        repositories = await self._github_service.get_user_repositories(github_token)
        return repositories
