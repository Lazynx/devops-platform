import uuid
from datetime import UTC, datetime

from project_service.domain.entities import (
    DeploymentStatus,
    Project,
    ProjectStatus,
    SecretsStatus,
)


def make_project(**overrides):
    now = datetime.now(UTC)
    defaults = dict(
        id=uuid.uuid4(),
        owner_id=str(uuid.uuid4()),
        name="proj",
        github_repo_url="https://github.com/o/r",
        root_directory="./",
        status=ProjectStatus.active,
        secrets_count=0,
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return Project(**defaults)


class TestProjectLifecycle:
    def test_pause_sets_status(self):
        p = make_project()
        p.pause()
        assert p.status == ProjectStatus.paused

    def test_activate_sets_status(self):
        p = make_project(status=ProjectStatus.paused)
        p.activate()
        assert p.status == ProjectStatus.active

    def test_soft_delete_sets_status(self):
        p = make_project()
        p.soft_delete()
        assert p.status == ProjectStatus.deleted

    def test_mark_ready(self):
        p = make_project()
        p.mark_ready()
        assert p.status == ProjectStatus.ready

    def test_mark_failed(self):
        p = make_project()
        p.mark_failed()
        assert p.status == ProjectStatus.failed


class TestProjectSecretsState:
    def test_mark_secrets_pending(self):
        p = make_project()
        p.mark_secrets_pending()
        assert p.secrets_status == SecretsStatus.pending

    def test_mark_secrets_creating(self):
        p = make_project()
        p.mark_secrets_creating()
        assert p.secrets_status == SecretsStatus.creating

    def test_mark_secrets_ready(self):
        p = make_project()
        p.mark_secrets_ready()
        assert p.secrets_status == SecretsStatus.ready

    def test_mark_secrets_failed_sets_error(self):
        p = make_project()
        p.mark_secrets_failed("vault unavailable")
        assert p.secrets_status == SecretsStatus.failed
        assert p.last_error_message == "vault unavailable"
        assert p.last_error_step == "secrets"


class TestProjectDeploymentState:
    def test_mark_deployment_pending(self):
        p = make_project()
        p.mark_deployment_pending()
        assert p.deployment_status == DeploymentStatus.pending

    def test_mark_deployment_creating(self):
        p = make_project()
        p.mark_deployment_creating()
        assert p.deployment_status == DeploymentStatus.creating

    def test_mark_deployment_ready_sets_config_id(self):
        p = make_project()
        config_id = uuid.uuid4()
        p.mark_deployment_ready(config_id)
        assert p.deployment_status == DeploymentStatus.ready
        assert p.deployment_config_id == config_id

    def test_mark_deployment_failed_sets_error(self):
        p = make_project()
        p.mark_deployment_failed("nomad unreachable")
        assert p.deployment_status == DeploymentStatus.failed
        assert p.last_error_message == "nomad unreachable"
        assert p.last_error_step == "deployment"
