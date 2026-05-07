import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def anyio_backend():
    return "asyncio"

from project_service.domain.entities import Project, ProjectStatus, SecretsStatus, DeploymentStatus


@pytest.fixture
def project_id():
    return uuid.uuid4()


@pytest.fixture
def owner_id():
    return uuid.uuid4()


def make_project(**kwargs):
    now = datetime.now(UTC)
    defaults = dict(
        id=uuid.uuid4(),
        owner_id=str(uuid.uuid4()),
        name="test-project",
        description=None,
        github_repo_url="https://github.com/owner/repo",
        language="Python",
        framework="FastAPI",
        root_directory="./",
        status=ProjectStatus.active,
        secrets_count=0,
        secrets_status=None,
        deployment_status=None,
        deployment_config_id=None,
        last_error_message=None,
        last_error_step=None,
        deployment_url=None,
        created_at=now,
        updated_at=now,
    )
    defaults.update(kwargs)
    return Project(**defaults)


@pytest.fixture
def test_project(project_id, owner_id):
    return make_project(id=project_id, owner_id=str(owner_id))


@pytest.fixture
def mock_project_repo():
    return AsyncMock()
