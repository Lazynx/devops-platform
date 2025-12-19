from dataclasses import dataclass
from uuid import UUID

from secrets_service.domain.entities import SecretType


@dataclass
class CreateSecretDTO:
    project_id: UUID
    key: str
    value: str
    secret_type: SecretType
    deployment_id: UUID | None = None
    description: str | None = None


@dataclass
class CreateBulkSecretsDTO:
    project_id: UUID
    secrets: list['SecretItemDTO']
    deployment_id: UUID | None = None


@dataclass
class SecretItemDTO:
    key: str
    value: str
    secret_type: SecretType
    description: str | None = None


@dataclass
class SecretDTO:
    id: UUID
    project_id: UUID
    deployment_id: UUID | None
    key: str
    secret_type: SecretType
    vault_path: str
    description: str | None


@dataclass
class SecretWithValueDTO:
    id: UUID
    project_id: UUID
    deployment_id: UUID | None
    key: str
    value: str
    secret_type: SecretType
    description: str | None


@dataclass
class UpdateSecretDTO:
    secret_id: UUID
    value: str
    description: str | None = None


@dataclass
class DeploymentCreatedEventDTO:
    deployment_id: UUID
    project_id: UUID
    config_id: UUID
