import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from secrets_service.application.dtos import CreateSecretDTO
from secrets_service.application.interactors.create_secret import CreateSecretInteractor
from secrets_service.domain.entities import SecretMetadata, SecretType


def make_saved_metadata(project_id, key):
    now = datetime.now(UTC)
    return SecretMetadata(
        id=uuid.uuid4(),
        project_id=project_id,
        deployment_id=None,
        key=key,
        vault_path=f"projects/{project_id}/{key}",
        secret_type=SecretType.ENV_VAR,
        description=None,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.anyio
async def test_create_secret_writes_to_vault_and_db():
    project_id = uuid.uuid4()
    dto = CreateSecretDTO(
        project_id=project_id,
        key="MY_KEY",
        value="secret-value",
        secret_type=SecretType.ENV_VAR,
    )
    saved = make_saved_metadata(project_id, "MY_KEY")

    repo = AsyncMock()
    vault = AsyncMock()
    publisher = AsyncMock()
    repo.save.return_value = saved
    vault.write_secret.return_value = None

    interactor = CreateSecretInteractor(repo, vault, publisher)
    result = await interactor.execute(dto)

    vault.write_secret.assert_called_once()
    repo.save.assert_called_once()
    assert result.key == "MY_KEY"
    assert result.project_id == project_id


@pytest.mark.anyio
async def test_create_secret_publishes_event():
    project_id = uuid.uuid4()
    dto = CreateSecretDTO(
        project_id=project_id,
        key="TOKEN",
        value="tok",
        secret_type=SecretType.API_KEY,
    )
    saved = make_saved_metadata(project_id, "TOKEN")

    repo = AsyncMock()
    vault = AsyncMock()
    publisher = AsyncMock()
    repo.save.return_value = saved

    interactor = CreateSecretInteractor(repo, vault, publisher)
    await interactor.execute(dto)

    publisher.publish_secret_created.assert_called_once()


@pytest.mark.anyio
async def test_create_secret_with_deployment_id_builds_correct_path():
    project_id = uuid.uuid4()
    deployment_id = uuid.uuid4()
    dto = CreateSecretDTO(
        project_id=project_id,
        key="DB_URL",
        value="postgres://...",
        secret_type=SecretType.DATABASE_URL,
        deployment_id=deployment_id,
    )
    saved = make_saved_metadata(project_id, "DB_URL")
    repo = AsyncMock()
    vault = AsyncMock()
    publisher = AsyncMock()
    repo.save.return_value = saved

    interactor = CreateSecretInteractor(repo, vault, publisher)
    await interactor.execute(dto)

    call_args = vault.write_secret.call_args
    path = call_args[0][0]
    assert str(project_id) in path
    assert str(deployment_id) in path
