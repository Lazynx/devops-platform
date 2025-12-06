from datetime import UTC, datetime
from enum import Enum as PyEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum as SqlEnum, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ProjectStatus(str, PyEnum):
    ACTIVE = 'active'
    PAUSED = 'paused'
    DELETED = 'deleted'


class Project(Base):
    __tablename__ = 'projects'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(String(255), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text(), nullable=True)

    github_repo_url: Mapped[str] = mapped_column(String(512), nullable=True, unique=True)
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
        default=ProjectStatus.ACTIVE,
        nullable=False
    )
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
        self.status = ProjectStatus.PAUSED
        self.updated_at = datetime.now(UTC)

    def activate(self) -> None:
        self.status = ProjectStatus.ACTIVE
        self.updated_at = datetime.now(UTC)

    def soft_delete(self) -> None:
        self.status = ProjectStatus.DELETED
        self.updated_at = datetime.now(UTC)
