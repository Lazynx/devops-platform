from datetime import UTC, datetime
from enum import Enum as PyEnum
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, Enum as SqlEnum, Float, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Environment(str, PyEnum):
    development = 'development'
    staging = 'staging'
    production = 'production'


class DeploymentStatus(str, PyEnum):
    pending = 'pending'
    building = 'building'
    deploying = 'deploying'
    running = 'running'
    failed = 'failed'
    stopped = 'stopped'


class DeploymentConfig(Base):
    __tablename__ = 'deployment_configs'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    github_repo_url: Mapped[str] = mapped_column(String(512), nullable=False)

    environment: Mapped[Environment] = mapped_column(
        SqlEnum(Environment),
        default=Environment.development,
        nullable=False
    )

    instance_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    cpu_limit: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    memory_limit: Mapped[int] = mapped_column(Integer, default=512, nullable=False)

    auto_scaling_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    min_instances: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_instances: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    port: Mapped[int] = mapped_column(Integer, default=8000, nullable=False)
    health_check_path: Mapped[str] = mapped_column(String(255), default='/health', nullable=False)

    dockerfile_path: Mapped[str] = mapped_column(String(255), default='./Dockerfile', nullable=False)
    docker_build_context: Mapped[str] = mapped_column(String(255), default='.', nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def update_resources(
        self,
        instance_count: int | None = None,
        cpu_limit: float | None = None,
        memory_limit: int | None = None
    ) -> None:
        if instance_count is not None:
            self.instance_count = instance_count
        if cpu_limit is not None:
            self.cpu_limit = cpu_limit
        if memory_limit is not None:
            self.memory_limit = memory_limit
        self.updated_at = datetime.now(UTC)

    def enable_auto_scaling(self, min_instances: int, max_instances: int) -> None:
        self.auto_scaling_enabled = True
        self.min_instances = min_instances
        self.max_instances = max_instances
        self.updated_at = datetime.now(UTC)

    def disable_auto_scaling(self) -> None:
        self.auto_scaling_enabled = False
        self.updated_at = datetime.now(UTC)


class Deployment(Base):
    __tablename__ = 'deployments'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    config_id: Mapped[UUID] = mapped_column(ForeignKey('deployment_configs.id'), nullable=False)
    project_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)

    version: Mapped[str] = mapped_column(String(255), nullable=False)
    commit_sha: Mapped[str] = mapped_column(String(255), nullable=True)
    image_url: Mapped[str] = mapped_column(String(512), nullable=True)
    deployment_url: Mapped[str] = mapped_column(String(512), nullable=True)

    status: Mapped[DeploymentStatus] = mapped_column(
        SqlEnum(DeploymentStatus),
        default=DeploymentStatus.pending,
        nullable=False
    )

    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    deployed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    stopped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def mark_building(self) -> None:
        self.status = DeploymentStatus.building
        self.updated_at = datetime.now(UTC)

    def mark_deploying(self) -> None:
        self.status = DeploymentStatus.deploying
        self.updated_at = datetime.now(UTC)

    def mark_running(self, image_url: str, deployment_url: str | None = None) -> None:
        self.status = DeploymentStatus.running
        self.image_url = image_url
        self.deployment_url = deployment_url
        self.deployed_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def mark_failed(self, error_message: str) -> None:
        self.status = DeploymentStatus.failed
        self.error_message = error_message
        self.updated_at = datetime.now(UTC)

    def mark_stopped(self) -> None:
        self.status = DeploymentStatus.stopped
        self.stopped_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

