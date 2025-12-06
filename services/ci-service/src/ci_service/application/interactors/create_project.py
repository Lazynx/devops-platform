from datetime import UTC, datetime
from uuid import uuid4

from ci_service.application.dtos import CreateProjectInputDTO, CreateProjectOutputDTO
from ci_service.application.interfaces.auth_service import IAuthService
from ci_service.application.interfaces.github_service import IGitHubService
from ci_service.application.interfaces.project_repository import IProjectRepository
from ci_service.domain.entities import Project, ProjectStatus


class ProjectAlreadyExistsError(Exception):
    def __init__(self, github_repo_url: str):
        self.github_repo_url = github_repo_url
        super().__init__(f"Project with GitHub URL '{github_repo_url}' already exists")


class CreateProjectInteractor:
    def __init__(
        self,
        project_repository: IProjectRepository,
        auth_service: IAuthService,
        github_service: IGitHubService,
        webhook_url: str,
    ):
        self._project_repo = project_repository
        self._auth_service = auth_service
        self._github_service = github_service
        self._webhook_url = webhook_url

    async def __call__(self, dto: CreateProjectInputDTO) -> CreateProjectOutputDTO:
        existing_project = await self._project_repo.get_by_github_repo_url(
            dto.github_repo_url
        )

        if existing_project:
            raise ProjectAlreadyExistsError(dto.github_repo_url)

        github_token = await self._auth_service.get_github_token(dto.user_access_token)

        # Try to create webhook if URL is publicly accessible
        webhook_id = None
        webhook_secret = None

        if not self._webhook_url.startswith('http://localhost') and not self._webhook_url.startswith('http://127.0.0.1'):
            try:
                webhook_data = await self._github_service.create_webhook(
                    github_token=github_token,
                    owner=dto.owner,
                    repo=dto.repo,
                    webhook_url=f"{self._webhook_url}/api/v1/webhooks/github",
                    events=['push', 'pull_request'],
                )
                webhook_id = webhook_data.github_webhook_id
                webhook_secret = webhook_data.github_webhook_secret
            except Exception as e:
                # Log warning but continue - webhook is not critical for MVP
                import logging
                logging.warning(f"Failed to create webhook for {dto.owner}/{dto.repo}: {e}")

        owner_id = await self._auth_service.get_current_user_id(dto.user_access_token)

        now = datetime.now(UTC)

        project = Project(
            id=uuid4(),
            owner_id=owner_id,
            name=dto.name,
            description=dto.description,
            github_repo_url=dto.github_repo_url,
            github_webhook_id=webhook_id,
            github_webhook_secret=webhook_secret,
            language=dto.language,
            framework=dto.framework,
            root_directory=dto.root_directory,
            install_command=dto.install_command,
            build_command=dto.build_command,
            start_command=dto.start_command,
            status=ProjectStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

        saved_project = await self._project_repo.save(project)

        return CreateProjectOutputDTO(**saved_project.__dict__)
