import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class GitHubClient:
    def __init__(self, workspace_dir: str = '/tmp/deployments'):
        self._workspace = Path(workspace_dir)
        self._workspace.mkdir(parents=True, exist_ok=True)

    async def clone_repository(
        self, repo_url: str, project_id: str, commit_sha: str | None = None, token: str | None = None
    ) -> str:
        project_dir = self._workspace / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        clone_url = repo_url
        if token:
            clone_url = repo_url.replace('https://', f'https://{token}@')

        try:
            logger.info(f'Cloning repository {repo_url} to {project_dir}')

            subprocess.run(['git', 'clone', clone_url, str(project_dir)], check=True, capture_output=True)

            if commit_sha:
                subprocess.run(
                    ['git', 'checkout', commit_sha], cwd=str(project_dir), check=True, capture_output=True
                )
                logger.info(f'Checked out commit {commit_sha}')

            logger.info(f'Repository cloned successfully to {project_dir}')
            return str(project_dir)

        except subprocess.CalledProcessError as e:
            logger.error(f'Git clone failed: {e.stderr.decode()}')
            raise RuntimeError(f'Failed to clone repository: {e.stderr.decode()}') from e

    async def cleanup_repository(self, project_id: str) -> None:
        project_dir = self._workspace / project_id
        if project_dir.exists():
            subprocess.run(['rm', '-rf', str(project_dir)], check=True)
            logger.info(f'Cleaned up repository at {project_dir}')
