import uuid
from datetime import UTC, datetime

import pytest

from project_service.application.exceptions import ProjectNotFoundError
from project_service.application.interactors.get_project_status import GetProjectStatusInteractor
from project_service.domain.entities import DeploymentStatus, Project, ProjectStatus, SecretsStatus


def make_project(**overrides):
    now = datetime.now(UTC)
    defaults = dict(
        id=uuid.uuid4(),
        owner_id=str(uuid.uuid4()),
        name="my-project",
        github_repo_url="https://github.com/o/r",
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
    defaults.update(overrides)
    return Project(**defaults)


@pytest.mark.anyio
async def test_get_status_project_not_found_raises(mock_project_repo):
    mock_project_repo.get_by_id.return_value = None
    interactor = GetProjectStatusInteractor(mock_project_repo)

    with pytest.raises(ProjectNotFoundError):
        await interactor.execute(uuid.uuid4())


@pytest.mark.anyio
async def test_get_status_simple_active_project(mock_project_repo):
    project = make_project(status=ProjectStatus.active)
    mock_project_repo.get_by_id.return_value = project
    interactor = GetProjectStatusInteractor(mock_project_repo)

    result = await interactor.execute(project.id)

    assert result.project_id == project.id
    assert result.status == "active"
    assert result.progress.total_steps == 1
    assert result.progress.completed_steps == 1
    assert result.progress.percentage == 100
    assert result.error is None


@pytest.mark.anyio
async def test_get_status_with_secrets_pending_counts_steps(mock_project_repo):
    project = make_project(
        status=ProjectStatus.secrets_pending,
        secrets_count=3,
        secrets_status=SecretsStatus.pending,
    )
    mock_project_repo.get_by_id.return_value = project
    interactor = GetProjectStatusInteractor(mock_project_repo)

    result = await interactor.execute(project.id)

    assert result.progress.total_steps == 2
    assert result.progress.completed_steps == 1
    assert result.progress.percentage == 50


@pytest.mark.anyio
async def test_get_status_all_ready_is_100_percent(mock_project_repo):
    config_id = uuid.uuid4()
    project = make_project(
        status=ProjectStatus.ready,
        secrets_count=2,
        secrets_status=SecretsStatus.ready,
        deployment_status=DeploymentStatus.ready,
        deployment_config_id=config_id,
    )
    mock_project_repo.get_by_id.return_value = project
    interactor = GetProjectStatusInteractor(mock_project_repo)

    result = await interactor.execute(project.id)

    assert result.progress.total_steps == 3
    assert result.progress.completed_steps == 3
    assert result.progress.percentage == 100


@pytest.mark.anyio
async def test_get_status_error_is_included(mock_project_repo):
    project = make_project(
        status=ProjectStatus.failed,
        last_error_message="Vault unreachable",
        last_error_step="secrets",
    )
    mock_project_repo.get_by_id.return_value = project
    interactor = GetProjectStatusInteractor(mock_project_repo)

    result = await interactor.execute(project.id)

    assert result.error is not None
    assert result.error.message == "Vault unreachable"
    assert result.error.step == "secrets"


@pytest.mark.anyio
async def test_get_status_initializing_current_step(mock_project_repo):
    project = make_project(status=ProjectStatus.initializing)
    mock_project_repo.get_by_id.return_value = project
    interactor = GetProjectStatusInteractor(mock_project_repo)

    result = await interactor.execute(project.id)

    assert "Initializing" in result.progress.current_step
