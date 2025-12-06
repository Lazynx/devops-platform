from uuid import UUID

from deployment_service.application.interfaces.deployment_executor import DeploymentExecutor


class StopDeploymentInteractor:
    def __init__(self, executor: DeploymentExecutor):
        self._executor = executor

    async def __call__(self, deployment_id: UUID) -> None:
        await self._executor.stop_deployment(deployment_id)
