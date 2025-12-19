from datetime import datetime, UTC
from uuid import UUID

from project_service.application.dtos import ProjectStatusDTO, ProgressDTO, ErrorDTO
from project_service.application.exceptions import ProjectNotFoundError
from project_service.application.interfaces.project_repository import IProjectRepository
from project_service.domain.entities import ProjectStatus, SecretsStatus, DeploymentStatus


class GetProjectStatusInteractor:
    def __init__(self, repository: IProjectRepository):
        self._repository = repository

    async def execute(self, project_id: UUID) -> ProjectStatusDTO:
        project = await self._repository.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundError(project_id)

        total_steps = 1
        completed_steps = 1

        if project.secrets_count > 0:
            total_steps += 1
            if project.secrets_status == SecretsStatus.ready:
                completed_steps += 1

        if project.deployment_status is not None:
            total_steps += 1
            if project.deployment_status == DeploymentStatus.ready:
                completed_steps += 1

        percentage = int((completed_steps / total_steps) * 100)

        current_step = self._determine_current_step(project)

        progress = ProgressDTO(
            current_step=current_step,
            total_steps=total_steps,
            completed_steps=completed_steps,
            percentage=percentage,
            secrets_count=project.secrets_count if project.secrets_count > 0 else None,
            deployment_config_id=project.deployment_config_id,
        )

        error = None
        if project.last_error_message:
            error = ErrorDTO(
                step=project.last_error_step or 'unknown',
                message=project.last_error_message,
                timestamp=project.updated_at,
            )

        return ProjectStatusDTO(
            project_id=project.id,
            name=project.name,
            status=project.status.value,
            updated_at=project.updated_at,
            secrets_status=project.secrets_status.value if project.secrets_status else None,
            deployment_status=project.deployment_status.value if project.deployment_status else None,
            deployment_url=project.deployment_url,
            progress=progress,
            error=error,
        )

    def _determine_current_step(self, project) -> str:
        if project.status == ProjectStatus.failed:
            return "Failed"

        if project.status == ProjectStatus.ready:
            return "Ready to deploy"

        if project.status == ProjectStatus.initializing:
            return "Initializing project..."

        if project.secrets_status == SecretsStatus.creating or project.secrets_status == SecretsStatus.pending:
            return "Creating secrets..."

        if project.deployment_status == DeploymentStatus.creating or project.deployment_status == DeploymentStatus.pending:
            return "Configuring deployment..."

        return "Processing..."
