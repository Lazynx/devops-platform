import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from secrets_service.application.interactors.get_secrets import (
    GetSecretsByProjectInteractor,
    GetSecretValueInteractor,
)
from secrets_service.domain.entities import SecretMetadata, SecretType


def make_secret_metadata(project_id=None, **overrides):
    now = datetime.now(UTC)
    defaults = dict(
        id=uuid.uuid4(),
        project_id=project_id or uuid.uuid4(),
        deployment_id=None,
        key="API_KEY",
        vault_path="projects/abc/API_KEY",
        secret_type=SecretType.API_KEY,
        description="test key",
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return SecretMetadata(**defaults)


@pytest.mark.anyio
async def test_get_by_project_returns_dtos():
    project_id = uuid.uuid4()
    secrets = [make_secret_metadata(project_id=project_id), make_secret_metadata(project_id=project_id)]

    repo = AsyncMock()
    repo.get_by_project_id.return_value = secrets

    interactor = GetSecretsByProjectInteractor(repo)
    result = await interactor.execute(project_id)

    assert len(result) == 2
    assert all(dto.project_id == project_id for dto in result)
    repo.get_by_project_id.assert_called_once_with(project_id)


@pytest.mark.anyio
async def test_get_by_project_empty_returns_empty_list():
    repo = AsyncMock()
    repo.get_by_project_id.return_value = []

    interactor = GetSecretsByProjectInteractor(repo)
    result = await interactor.execute(uuid.uuid4())

    assert result == []


@pytest.mark.anyio
async def test_get_secret_value_success():
    secret = make_secret_metadata()
    repo = AsyncMock()
    vault = AsyncMock()
    repo.get_by_id.return_value = secret
    vault.read_secret.return_value = {"value": "my-secret-value"}

    interactor = GetSecretValueInteractor(repo, vault)
    result = await interactor.execute(secret.id)

    assert result.value == "my-secret-value"
    assert result.key == secret.key
    vault.read_secret.assert_called_once_with(secret.vault_path)


@pytest.mark.anyio
async def test_get_secret_value_not_found_raises():
    repo = AsyncMock()
    vault = AsyncMock()
    repo.get_by_id.return_value = None

    interactor = GetSecretValueInteractor(repo, vault)

    with pytest.raises(ValueError, match="not found"):
        await interactor.execute(uuid.uuid4())
