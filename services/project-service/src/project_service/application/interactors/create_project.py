import logging
from datetime import UTC, datetime
from uuid import uuid4

from project_service.application.dtos import CreateProjectInputDTO, CreateProjectOutputDTO
from project_service.application.interfaces.auth_service import IAuthService
from project_service.application.interfaces.github_service import IGitHubService
from project_service.application.interfaces.project_repository import IProjectRepository
from project_service.domain.entities import Project, ProjectStatus
from project_service.infrastructure.messaging.pending_configs_store import PendingConfigsStore
from project_service.infrastructure.messaging.publisher import ProjectEventPublisher

logger = logging.getLogger(__name__)


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
        event_publisher: ProjectEventPublisher,
        pending_configs_store: PendingConfigsStore,
    ):
        self._project_repo = project_repository
        self._auth_service = auth_service
        self._github_service = github_service
        self._webhook_url = webhook_url
        self._event_publisher = event_publisher
        self._pending_configs_store = pending_configs_store

    async def __call__(self, dto: CreateProjectInputDTO) -> CreateProjectOutputDTO:

        github_token = await self._auth_service.get_github_token(dto.user_access_token)

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
                logger.warning("Failed to create webhook for %s/%s: %s", dto.owner, dto.repo, e)

        owner_id = await self._auth_service.get_current_user_id(dto.user_access_token)

        now = datetime.now(UTC)

        has_secrets = dto.secrets and len(dto.secrets) > 0
        has_deployment_config = dto.deployment_config is not None

        initial_status = ProjectStatus.initializing if (has_secrets or has_deployment_config) else ProjectStatus.active

        project = Project(
            id=uuid4(),
            owner_id=str(owner_id),
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
            status=initial_status,
            secrets_count=len(dto.secrets) if has_secrets else 0,
            secrets_status=None,
            deployment_status=None,
            deployment_config_id=None,
            last_error_message=None,
            last_error_step=None,
            created_at=now,
            updated_at=now,
        )

        if has_secrets:
            project.mark_secrets_pending()

        if has_deployment_config:
            project.mark_deployment_pending()

        saved_project = await self._project_repo.save(project)

        logger.info(f"Creating project {saved_project.name} with {len(dto.secrets) if has_secrets else 0} secrets")

        if has_secrets or has_deployment_config:
            correlation_id = await self._event_publisher.publish_project_created_with_secrets(
                project_id=saved_project.id,
                owner_id=saved_project.owner_id,
                name=saved_project.name,
                github_repo_url=saved_project.github_repo_url,
                github_token=github_token,
                start_command=dto.start_command or "python manage.py runserver 0.0.0.0:$PORT",
                framework=saved_project.framework,
                secrets=dto.secrets or [],
                deployment_config=dto.deployment_config,
                auto_deploy=dto.auto_deploy,
            )

            if has_deployment_config:
                self._pending_configs_store.store(
                    project_id=saved_project.id,
                    deployment_config=dto.deployment_config,
                    user_token=dto.user_access_token,
                    auto_deploy=dto.auto_deploy,
                )
        else:
            await self._event_publisher.publish_project_created(
                project_id=saved_project.id,
                owner_id=saved_project.owner_id,
                name=saved_project.name,
                github_repo_url=saved_project.github_repo_url,
                framework=saved_project.framework,
            )

        return CreateProjectOutputDTO(
            id=saved_project.id,
            owner_id=saved_project.owner_id,
            name=saved_project.name,
            description=saved_project.description,
            github_repo_url=saved_project.github_repo_url,
            github_webhook_id=saved_project.github_webhook_id or 0,
            language=saved_project.language,
            framework=saved_project.framework,
            root_directory=saved_project.root_directory,
            install_command=saved_project.install_command,
            build_command=saved_project.build_command,
            start_command=saved_project.start_command,
            status=saved_project.status.value,
            created_at=saved_project.created_at,
            updated_at=saved_project.updated_at,
            requires_polling=initial_status == ProjectStatus.initializing,
            secrets_status=saved_project.secrets_status.value if saved_project.secrets_status else None,
            deployment_status=saved_project.deployment_status.value if saved_project.deployment_status else None,
        )
