from datetime import UTC, datetime
from enum import Enum as PyEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum as SqlEnum, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ProjectStatus(str, PyEnum):
    initializing = 'initializing'
    secrets_pending = 'secrets_pending'
    deployment_pending = 'deployment_pending'
    ready = 'ready'
    active = 'active'
    paused = 'paused'
    deleted = 'deleted'
    failed = 'failed'


class SecretsStatus(str, PyEnum):
    pending = 'pending'
    creating = 'creating'
    ready = 'ready'
    failed = 'failed'


class DeploymentStatus(str, PyEnum):
    pending = 'pending'
    creating = 'creating'
    ready = 'ready'
    failed = 'failed'


class Project(Base):
    __tablename__ = 'projects'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(String(255), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text(), nullable=True)

    github_repo_url: Mapped[str] = mapped_column(String(512), nullable=True)
    github_webhook_id: Mapped[int] = mapped_column(Integer, nullable=True)
    github_webhook_secret: Mapped[str] = mapped_column(String(512), nullable=True)

    language: Mapped[str] = mapped_column(String(255), nullable=True)
    framework: Mapped[str] = mapped_column(String(255), nullable=True)
    root_directory: Mapped[str] = mapped_column(String(255), default='./', nullable=False)
    install_command: Mapped[str] = mapped_column(String(255), nullable=True)
    build_command: Mapped[str] = mapped_column(String(255), nullable=True)
    start_command: Mapped[str] = mapped_column(String(255), nullable=True)

    status: Mapped[ProjectStatus] = mapped_column(
        SqlEnum(ProjectStatus),
        default=ProjectStatus.active,
        nullable=False
    )

    deployment_config_id: Mapped[UUID | None] = mapped_column(nullable=True)
    secrets_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    secrets_status: Mapped[SecretsStatus | None] = mapped_column(
        SqlEnum(SecretsStatus),
        nullable=True
    )
    deployment_status: Mapped[DeploymentStatus | None] = mapped_column(
        SqlEnum(DeploymentStatus),
        nullable=True
    )
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_error_step: Mapped[str | None] = mapped_column(String(50), nullable=True)
    deployment_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

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

    def pause(self) -> None:
        self.status = ProjectStatus.paused
        self.updated_at = datetime.now(UTC)

    def activate(self) -> None:
        self.status = ProjectStatus.active
        self.updated_at = datetime.now(UTC)

    def soft_delete(self) -> None:
        self.status = ProjectStatus.deleted
        self.updated_at = datetime.now(UTC)

    def mark_secrets_pending(self) -> None:
        self.secrets_status = SecretsStatus.pending
        self.updated_at = datetime.now(UTC)

    def mark_secrets_creating(self) -> None:
        self.secrets_status = SecretsStatus.creating
        self.updated_at = datetime.now(UTC)

    def mark_secrets_ready(self) -> None:
        self.secrets_status = SecretsStatus.ready
        self.updated_at = datetime.now(UTC)

    def mark_secrets_failed(self, error: str) -> None:
        self.secrets_status = SecretsStatus.failed
        self.last_error_message = error
        self.last_error_step = 'secrets'
        self.updated_at = datetime.now(UTC)

    def mark_deployment_pending(self) -> None:
        self.deployment_status = DeploymentStatus.pending
        self.updated_at = datetime.now(UTC)

    def mark_deployment_creating(self) -> None:
        self.deployment_status = DeploymentStatus.creating
        self.updated_at = datetime.now(UTC)

    def mark_deployment_ready(self, config_id: UUID) -> None:
        self.deployment_status = DeploymentStatus.ready
        self.deployment_config_id = config_id
        self.updated_at = datetime.now(UTC)

    def mark_deployment_failed(self, error: str) -> None:
        self.deployment_status = DeploymentStatus.failed
        self.last_error_message = error
        self.last_error_step = 'deployment'
        self.updated_at = datetime.now(UTC)

    def mark_ready(self) -> None:
        self.status = ProjectStatus.ready
        self.updated_at = datetime.now(UTC)

    def mark_failed(self) -> None:
        self.status = ProjectStatus.failed
        self.updated_at = datetime.now(UTC)
