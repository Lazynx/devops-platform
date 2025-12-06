import logging
import secrets
from datetime import datetime

import httpx

from ci_service.application.dtos import GitHubRepositoryDTO, GitHubWebhookDTO, RepositoryFileDTO
from ci_service.application.interfaces.github_service import IGitHubService

logger = logging.getLogger(__name__)


class GitHubServiceImpl(IGitHubService):
    def __init__(self, client: httpx.AsyncClient, github_api_url: str):
        self._client = client
        self._github_api_url = github_api_url

    async def get_user_repositories(self, github_token: str) -> list[GitHubRepositoryDTO]:
        headers = {
            'Authorization': f'Bearer {github_token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
        }

        try:
            response = await self._client.get(
                url=self._github_api_url + '/user/repos',
                headers=headers,
                params={
                    'per_page': 100,
                    'sort': 'updated',
                    'direction': 'desc',
                },
            )
            response.raise_for_status()

            repos_data = response.json()

            repositories = [self._map_repo_to_dto(repo) for repo in repos_data]

            logger.info(f'Retrieved {len(repositories)} repositories from GitHub')
            return repositories

        except httpx.HTTPStatusError as e:
            logger.error(f'GitHub API error: {e.response.status_code} - {e.response.text}')
            raise
        except Exception as e:
            logger.error(f'Unexpected error calling GitHub API: {e}')
            raise

    async def get_repo_contents(
        self,
        github_token: str,
        owner: str,
        repo: str,
        path: str = ''
    ) -> list[RepositoryFileDTO]:
        headers = {
            'Authorization': f'Bearer {github_token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
        }

        normalized_path = path.strip('./').strip('/')

        url = self._github_api_url + f'/repos/{owner}/{repo}/contents/'
        if normalized_path:
            url += normalized_path

        try:
            response = await self._client.get(url=url, headers=headers)
            response.raise_for_status()

            files_data = response.json()

            files = [self._map_file_to_dto(file) for file in files_data]

            logger.info(f'Retrieved {len(files)} files from {owner}/{repo}/{path or "root"}')
            return files

        except httpx.HTTPStatusError as e:
            logger.error(f'GitHub API error: {e.response.status_code} - {e.response.text}')
            raise
        except Exception as e:
            logger.error(f'Unexpected error calling GitHub API: {e}')
            raise

    async def get_file_content(
        self,
        github_token: str,
        owner: str,
        repo: str,
        file_path: str
    ) -> str | None:
        headers = {
            'Authorization': f'Bearer {github_token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
        }

        try:
            response = await self._client.get(
                f'{self._github_api_url}/repos/{owner}/{repo}/contents/{file_path}',
                headers=headers,
            )
            response.raise_for_status()

            file_data = response.json()

            import base64
            if 'content' in file_data:
                content = base64.b64decode(file_data['content']).decode('utf-8')
                return content

            return None

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug(f'File {file_path} not found in {owner}/{repo}')
                return None
            logger.error(f'GitHub API error: {e.response.status_code} - {e.response.text}')
            return None
        except Exception as e:
            logger.error(f'Error getting file content: {e}')
            return None

    async def create_webhook(
        self,
        github_token: str,
        owner: str,
        repo: str,
        webhook_url: str,
        events: list[str],
    ) -> GitHubWebhookDTO:
        headers = {
            'Authorization': f'Bearer {github_token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
        }

        webhook_secret = secrets.token_urlsafe(32)

        payload = {
            'config': {
                'url': webhook_url,
                'content_type': 'json',
                'secret': webhook_secret,
                'insecure_ssl': '1'
            },
            'events': events,
            'active': True,
        }

        url = f'{self._github_api_url}/repos/{owner}/{repo}/hooks'

        try:
            response = await self._client.post(
                url=url,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()

            hook_data = response.json()
            logger.info(f'Created webhook for {owner}/{repo}/{webhook_url} - {hook_data}')
            return GitHubWebhookDTO(
                webhook_id=hook_data['id'],
                webhook_secret=webhook_secret,
                webhook_url=hook_data['config']['url'],
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.error(f'Repository {owner}/{repo} not found')
            elif e.response.status_code == 403:
                logger.error(
                    f'Permission denied to create webhook for {owner}/{repo}. '
                    f'User needs admin access to the repository.'
                )
            elif e.response.status_code == 422:
                logger.warning(
                    f'Webhook for {owner}/{repo} might already exist: '
                    f'{e.response.text}'
                )
            else:
                logger.error(
                    f'GitHub API error: {e.response.status_code} - '
                    f'{e.response.text}'
                )
            raise
        except Exception as e:
            logger.error(f'Unexpected error creating webhook: {e}')
            raise


    def _map_repo_to_dto(self, repo_data: dict) -> GitHubRepositoryDTO:
        return GitHubRepositoryDTO(
            id=repo_data['id'],
            name=repo_data['name'],
            full_name=repo_data['full_name'],
            private=repo_data['private'],
            html_url=repo_data['html_url'],
            description=repo_data.get('description'),
            fork=repo_data['fork'],
            created_at=self._parse_datetime(repo_data['created_at']),
            updated_at=self._parse_datetime(repo_data['updated_at']),
            pushed_at=self._parse_datetime(repo_data.get('pushed_at')) if repo_data.get('pushed_at') else None,
            size=repo_data['size'],
            stargazers_count=repo_data['stargazers_count'],
            watchers_count=repo_data['watchers_count'],
            language=repo_data.get('language'),
            forks_count=repo_data['forks_count'],
            open_issues_count=repo_data['open_issues_count'],
            default_branch=repo_data['default_branch'],
        )

    @staticmethod
    def _map_file_to_dto(file_data: dict) -> RepositoryFileDTO:
        return RepositoryFileDTO(
            name=file_data['name'],
            path=file_data['path'],
            type=file_data['type'],
        )

    @staticmethod
    def _parse_datetime(datetime_str: str) -> datetime:
        return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
