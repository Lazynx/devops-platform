from abc import ABC, abstractmethod

from ci_service.application.dtos import GitHubRepositoryDTO, GitHubWebhookDTO, RepositoryFileDTO


class IGitHubService(ABC):
    @abstractmethod
    async def get_user_repositories(self, github_token: str) -> list[GitHubRepositoryDTO]:
        raise NotImplementedError()

    @abstractmethod
    async def get_repo_contents(
        self,
        github_token: str,
        owner: str,
        repo: str,
        path: str = ''
    ) -> list[RepositoryFileDTO]:
        raise NotImplementedError()

    @abstractmethod
    async def get_file_content(
        self,
        github_token: str,
        owner: str,
        repo: str,
        file_path: str
    ) -> str | None:
        raise NotImplementedError()

    @abstractmethod
    async def create_webhook(
        self,
        github_token: str,
        owner: str,
        repo: str,
        webhook_url: str,
        events: list[str],
    ) -> GitHubWebhookDTO:
        raise NotImplementedError()
