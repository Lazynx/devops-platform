from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateDeploymentConfigRequest(BaseModel):
    project_id: UUID
    environment: str = Field(..., pattern='^(development|staging|production)$')
    instance_count: int = Field(default=1, ge=1, le=20)
    cpu_limit: float = Field(default=1.0, ge=0.1, le=16.0)
    memory_limit: int = Field(default=512, ge=128, le=32768)
    auto_scaling_enabled: bool = Field(default=False)
    min_instances: int = Field(default=1, ge=1)
    max_instances: int = Field(default=10, ge=1, le=50)
    port: int = Field(default=8000, ge=1, le=65535)
    health_check_path: str = Field(default='/health')
    env_variables: dict[str, str] = Field(default_factory=dict)
    dockerfile_path: str = Field(default='./Dockerfile')
    docker_build_context: str = Field(default='.')


class DeploymentConfigResponse(BaseModel):
    id: UUID
    project_id: UUID
    environment: str
    instance_count: int
    cpu_limit: float
    memory_limit: int
    auto_scaling_enabled: bool
    min_instances: int
    max_instances: int
    port: int
    health_check_path: str
    env_variables: dict[str, str]
    dockerfile_path: str
    docker_build_context: str
    created_at: datetime
    updated_at: datetime


class CreateDeploymentRequest(BaseModel):
    config_id: UUID
    version: str
    commit_sha: str | None = None


class DeploymentResponse(BaseModel):
    id: UUID
    config_id: UUID
    project_id: UUID
    version: str
    commit_sha: str | None
    status: str
    created_at: datetime


class DeploymentStatusResponse(BaseModel):
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


class DeploymentDetailResponse(BaseModel):
    id: UUID
    config_id: UUID
    project_id: UUID
    version: str
    commit_sha: str | None
    image_url: str | None
    status: str
    error_message: str | None
    deployed_at: datetime | None
    stopped_at: datetime | None
    created_at: datetime
    updated_at: datetime


class DeploymentLogsResponse(BaseModel):
    logs: str
