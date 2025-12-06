from uuid import UUID

from deployment_service.application.interfaces.deployment_executor import DeploymentExecutor


class GetDeploymentLogsInteractor:
    def __init__(self, executor: DeploymentExecutor):
        self._executor = executor

    async def __call__(self, deployment_id: UUID, tail: int = 100) -> str:
        return await self._executor.get_deployment_logs(deployment_id, tail)
