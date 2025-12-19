from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True, frozen=True)
class CreateDeploymentConfigInputDTO:
    user_access_token: str
    project_id: UUID
    github_repo_url: str
    environment: str
    instance_count: int
    cpu_limit: float
    memory_limit: int
    auto_scaling_enabled: bool
    min_instances: int
    max_instances: int
    port: int
    health_check_path: str
    dockerfile_path: str
    docker_build_context: str


@dataclass(slots=True, frozen=True)
class CreateDeploymentConfigOutputDTO:
    id: UUID
    project_id: UUID
    github_repo_url: str
    environment: str
    instance_count: int
    cpu_limit: float
    memory_limit: int
    auto_scaling_enabled: bool
    min_instances: int
    max_instances: int
    port: int
    health_check_path: str
    dockerfile_path: str
    docker_build_context: str
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True, frozen=True)
class UpdateDeploymentConfigInputDTO:
    user_access_token: str
    config_id: UUID
    instance_count: int | None = None
    cpu_limit: float | None = None
    memory_limit: int | None = None
    auto_scaling_enabled: bool | None = None
    min_instances: int | None = None
    max_instances: int | None = None


@dataclass(slots=True, frozen=True)
class CreateDeploymentInputDTO:
    user_access_token: str
    config_id: UUID
    version: str
    commit_sha: str | None = None


@dataclass(slots=True, frozen=True)
class CreateDeploymentOutputDTO:
    id: UUID
    config_id: UUID
    project_id: UUID
    version: str
    commit_sha: str | None
    status: str
    created_at: datetime


@dataclass(slots=True, frozen=True)
class DeploymentStatusDTO:
    id: UUID
    config_id: UUID
    project_id: UUID
    version: str
    status: str
    image_url: str | None
    error_message: str | None
    deployed_at: datetime | None
    stopped_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True, frozen=True)
class GetDeploymentOutputDTO:
    id: UUID
    config_id: UUID
    project_id: UUID
    version: str
    commit_sha: str | None
    image_url: str | None
    deployment_url: str | None
    status: str
    error_message: str | None
    deployed_at: datetime | None
    stopped_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True, frozen=True)
class ProjectCreatedEventDTO:
    project_id: UUID
    owner_id: UUID
    name: str
    github_repo_url: str
    framework: str | None
