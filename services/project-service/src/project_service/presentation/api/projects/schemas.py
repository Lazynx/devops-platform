from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from project_service.application.dtos import (
    CreateProjectInputDTO,
    DeploymentConfigDTO,
    ProjectSecretDTO,
)


class ProjectSecretItem(BaseModel):
    key: str = Field(..., min_length=1, max_length=255)
    value: str = Field(..., min_length=1)
    secret_type: str
    description: str | None = None

    def to_dto(self) -> ProjectSecretDTO:
        return ProjectSecretDTO(
            key=self.key,
            value=self.value,
            secret_type=self.secret_type,
            description=self.description,
        )


class DeploymentConfigRequest(BaseModel):
    environment: str
    instance_count: int = Field(..., ge=1)
    cpu_limit: float = Field(..., gt=0)
    memory_limit: int = Field(..., gt=0)
    port: int = Field(..., ge=1, le=65535)
    health_check_path: str
    dockerfile_path: str
    docker_build_context: str = "./"
    auto_scaling_enabled: bool = False
    min_instances: int = Field(default=1, ge=1)
    max_instances: int = Field(default=10, ge=1)

    def to_dto(self) -> DeploymentConfigDTO:
        return DeploymentConfigDTO(**self.model_dump())


class CreateProjectRequest(BaseModel):
    name: str
    owner: str
    repo: str
    github_repo_url: str
    language: str | None = None
    framework: str | None = None
    root_directory: str = './'
    install_command: str | None = None
    build_command: str | None = None
    start_command: str | None = None
    description: str | None = None
    secrets: list[ProjectSecretItem] | None = None
    deployment_config: DeploymentConfigRequest | None = None
    auto_deploy: bool = False

    def to_input_dto(self, user_access_token: str) -> CreateProjectInputDTO:
        return CreateProjectInputDTO(
            user_access_token=user_access_token,
            name=self.name,
            owner=self.owner,
            repo=self.repo,
            github_repo_url=self.github_repo_url,
            language=self.language,
            framework=self.framework,
            root_directory=self.root_directory,
            install_command=self.install_command,
            build_command=self.build_command,
            start_command=self.start_command,
            description=self.description,
            secrets=[s.to_dto() for s in self.secrets] if self.secrets else None,
            deployment_config=self.deployment_config.to_dto() if self.deployment_config else None,
            auto_deploy=self.auto_deploy,
        )


class ProjectResponse(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    description: str | None
    github_repo_url: str
    github_webhook_id: int
    language: str | None
    framework: str | None
    root_directory: str
    install_command: str | None
    build_command: str | None
    start_command: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    requires_polling: bool
    secrets_status: str | None = None
    deployment_status: str | None = None
    deployment_config_id: UUID | None = None

    model_config = {'from_attributes': True}


class ErrorResponse(BaseModel):
    step: str
    message: str
    timestamp: datetime


class ProgressResponse(BaseModel):
    current_step: str
    total_steps: int
    completed_steps: int
    percentage: int
    secrets_count: int | None = None
    deployment_config_id: UUID | None = None


class ProjectStatusResponse(BaseModel):
    project_id: UUID
    name: str
    status: str
    updated_at: datetime
    secrets_status: str | None
    deployment_status: str | None
    deployment_url: str | None
    progress: ProgressResponse
    error: ErrorResponse | None
