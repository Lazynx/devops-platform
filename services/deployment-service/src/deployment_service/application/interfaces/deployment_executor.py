from abc import ABC, abstractmethod
from uuid import UUID


class DeploymentExecutor(ABC):
    @abstractmethod
    async def execute_deployment(self, deployment_id: UUID) -> None:
        pass

    @abstractmethod
    async def stop_deployment(self, deployment_id: UUID) -> None:
        pass

    @abstractmethod
    async def get_deployment_logs(self, deployment_id: UUID, tail: int) -> str:
        pass
