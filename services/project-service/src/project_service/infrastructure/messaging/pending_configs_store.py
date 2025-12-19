from uuid import UUID

from project_service.application.dtos import DeploymentConfigDTO


class PendingConfigsStore:
    def __init__(self):
        self._pending_configs: dict[str, tuple[DeploymentConfigDTO, str, bool]] = {}

    def store(
        self,
        project_id: UUID,
        deployment_config: DeploymentConfigDTO,
        user_token: str,
        auto_deploy: bool,
    ) -> None:
        self._pending_configs[str(project_id)] = (deployment_config, user_token, auto_deploy)

    def pop(self, project_id: UUID) -> tuple[DeploymentConfigDTO, str, bool] | None:
        return self._pending_configs.pop(str(project_id), None)
