from datetime import UTC, datetime
from enum import Enum as PyEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum as SqlEnum, String, Text, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SecretType(str, PyEnum):
    ENV_VAR = 'env_var'
    API_KEY = 'api_key'
    DATABASE_URL = 'database_url'
    CERTIFICATE = 'certificate'


class SecretMetadata(Base):
    __tablename__ = 'secret_metadata'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    deployment_id: Mapped[UUID] = mapped_column(Uuid, nullable=True, index=True)

    key: Mapped[str] = mapped_column(String(255), nullable=False)
    vault_path: Mapped[str] = mapped_column(String(512), nullable=False)

    secret_type: Mapped[SecretType] = mapped_column(
        SqlEnum(SecretType), default=SecretType.ENV_VAR, nullable=False
    )

    description: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def update_vault_path(self, new_path: str) -> None:
        self.vault_path = new_path
        self.updated_at = datetime.now(UTC)
