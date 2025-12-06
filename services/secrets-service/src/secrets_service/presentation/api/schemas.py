from uuid import UUID

from pydantic import BaseModel, Field

from secrets_service.application.dtos import SecretDTO, SecretWithValueDTO
from secrets_service.domain.entities import SecretType


class CreateSecretRequest(BaseModel):
    project_id: UUID
    deployment_id: UUID | None = None
    key: str = Field(..., min_length=1, max_length=255)
    value: str = Field(..., min_length=1)
    secret_type: SecretType = SecretType.ENV_VAR
    description: str | None = None


class UpdateSecretRequest(BaseModel):
    value: str = Field(..., min_length=1)
    description: str | None = None


class SecretResponse(BaseModel):
    id: UUID
    project_id: UUID
    deployment_id: UUID | None
    key: str
    secret_type: SecretType
    vault_path: str
    description: str | None

    @classmethod
    def from_dto(cls, dto: SecretDTO) -> 'SecretResponse':
        return cls(
            id=dto.id,
            project_id=dto.project_id,
            deployment_id=dto.deployment_id,
            key=dto.key,
            secret_type=dto.secret_type,
            vault_path=dto.vault_path,
            description=dto.description,
        )


class SecretWithValueResponse(BaseModel):
    id: UUID
    project_id: UUID
    deployment_id: UUID | None
    key: str
    value: str
    secret_type: SecretType
    description: str | None

    @classmethod
    def from_dto(cls, dto: SecretWithValueDTO) -> 'SecretWithValueResponse':
        return cls(
            id=dto.id,
            project_id=dto.project_id,
            deployment_id=dto.deployment_id,
            key=dto.key,
            value=dto.value,
            secret_type=dto.secret_type,
            description=dto.description,
        )


class DeleteSecretResponse(BaseModel):
    message: str
