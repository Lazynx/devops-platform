from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True, frozen=True)
class GitHubRepositoryDTO:
    id: int
    name: str
    full_name: str
    private: bool
    html_url: str
    description: str | None
    fork: bool
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime | None
    size: int
    stargazers_count: int
    watchers_count: int
    language: str | None
    forks_count: int
    open_issues_count: int
    default_branch: str


@dataclass(slots=True, frozen=True)
class RepositoryConfigDTO:
    repository: str
    root_directory: str
    framework: str
    confidence: str
    install_command: str | None
    build_command: str | None
    start_command: str | None
    detected_files: list[str]


@dataclass(slots=True, frozen=True)
class RepositoryFileDTO:
    name: str
    path: str
    type: str


@dataclass(slots=True, frozen=True)
class AnalyzeRepositoryInputDTO:
    user_access_token: str
    owner: str
    repo: str
    root_directory: str


@dataclass(slots=True, frozen=True)
class AnalyzeRepositoryOutputDTO:
    repository: str
    root_directory: str
    framework: str
    confidence: str
    install_command: str | None
    build_command: str | None
    start_command: str | None
    detected_files: list[str]


@dataclass(slots=True, frozen=True)
class ProjectSecretDTO:
    key: str
    value: str
    secret_type: str
    description: str | None = None


@dataclass(slots=True, frozen=True)
class DeploymentConfigDTO:
    environment: str
    instance_count: int
    cpu_limit: float
    memory_limit: int
    port: int
    health_check_path: str
    dockerfile_path: str
    docker_build_context: str
    auto_scaling_enabled: bool
    min_instances: int
    max_instances: int


@dataclass(slots=True, frozen=True)
class CreateProjectInputDTO:
    user_access_token: str
    name: str
    owner: str
    repo: str
    github_repo_url: str
    language: str | None
    framework: str | None
    root_directory: str
    install_command: str | None
    build_command: str | None
    start_command: str | None
    description: str | None = None
    secrets: list[ProjectSecretDTO] | None = None
    deployment_config: DeploymentConfigDTO | None = None
    auto_deploy: bool = False


@dataclass(slots=True, frozen=True)
class CreateProjectOutputDTO:
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


@dataclass(slots=True, frozen=True)
class ErrorDTO:
    step: str
    message: str
    timestamp: datetime


@dataclass(slots=True, frozen=True)
class ProgressDTO:
    current_step: str
    total_steps: int
    completed_steps: int
    percentage: int
    secrets_count: int | None = None
    deployment_config_id: UUID | None = None


@dataclass(slots=True, frozen=True)
class ProjectStatusDTO:
    project_id: UUID
    name: str
    status: str
    updated_at: datetime
    secrets_status: str | None
    deployment_status: str | None
    deployment_url: str | None
    progress: ProgressDTO
    error: ErrorDTO | None

@dataclass(slots=True, frozen=True)
class GitHubWebhookDTO:
    webhook_id: int
    webhook_secret: str
    webhook_url: str


@dataclass(slots=True, frozen=True)
class ProjectDTO:
    id: UUID
    name: str
    github_repo_url: str
    owner_id: UUID
    status: str
    secrets_status: str | None
    deployment_status: str | None
    created_at: datetime
    updated_at: datetime
    description: str | None = None
    github_webhook_id: int = 0
    language: str | None = None
    framework: str | None = None
    root_directory: str = './'
    install_command: str | None = None
    build_command: str | None = None
    start_command: str | None = None
    requires_polling: bool = False
    deployment_config_id: UUID | None = None

