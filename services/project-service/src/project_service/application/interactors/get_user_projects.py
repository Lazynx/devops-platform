from uuid import UUID

from project_service.application.dtos import ProjectDTO
from project_service.application.interfaces.auth_service import IAuthService
from project_service.application.interfaces.project_repository import IProjectRepository


class GetUserProjectsInteractor:
    def __init__(
        self,
        project_repository: IProjectRepository,
        auth_service: IAuthService,
    ):
        self._project_repo = project_repository
        self._auth_service = auth_service

    async def execute(self, user_access_token: str) -> list[ProjectDTO]:
        user_id = await self._auth_service.get_current_user_id(user_access_token)
        projects = await self._project_repo.get_by_owner_id(user_id)

        return [
            ProjectDTO(
                id=project.id,
                name=project.name,
                github_repo_url=project.github_repo_url,
                owner_id=project.owner_id,
                status=project.status.value,
                secrets_status=project.secrets_status.value if project.secrets_status else None,
                deployment_status=project.deployment_status.value if project.deployment_status else None,
                created_at=project.created_at,
                updated_at=project.updated_at,
                description=project.description,
                github_webhook_id=project.github_webhook_id or 0,
                language=project.language,
                framework=project.framework,
                root_directory=project.root_directory,
                install_command=project.install_command,
                build_command=project.build_command,
                start_command=project.start_command,
                requires_polling=False,
                deployment_config_id=project.deployment_config_id,
            )
            for project in projects
        ]
