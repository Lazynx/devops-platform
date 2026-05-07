import uuid
from datetime import UTC, datetime

from secrets_service.domain.entities import SecretMetadata, SecretType


def make_secret(**overrides):
    now = datetime.now(UTC)
    defaults = dict(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        deployment_id=None,
        key="DATABASE_URL",
        vault_path="projects/abc/DATABASE_URL",
        secret_type=SecretType.ENV_VAR,
        description=None,
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return SecretMetadata(**defaults)


class TestSecretMetadata:
    def test_update_vault_path_changes_path(self):
        secret = make_secret(vault_path="old/path")
        secret.update_vault_path("new/path")
        assert secret.vault_path == "new/path"

    def test_update_vault_path_updates_timestamp(self):
        old_time = datetime(2020, 1, 1, tzinfo=UTC)
        secret = make_secret(updated_at=old_time)
        secret.update_vault_path("new/path")
        assert secret.updated_at > old_time


class TestSecretType:
    def test_enum_values(self):
        assert SecretType.ENV_VAR == "env_var"
        assert SecretType.API_KEY == "api_key"
        assert SecretType.DATABASE_URL == "database_url"
        assert SecretType.CERTIFICATE == "certificate"

    def test_is_string(self):
        assert isinstance(SecretType.ENV_VAR, str)
