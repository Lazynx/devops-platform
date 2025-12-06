from abc import ABC, abstractmethod
from uuid import UUID

from deployment_service.domain.entities import Deployment, DeploymentConfig


class IDeploymentConfigRepository(ABC):
    @abstractmethod
    async def save(self, config: DeploymentConfig) -> DeploymentConfig:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, config_id: UUID) -> DeploymentConfig | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_project_id(self, project_id: UUID) -> list[DeploymentConfig]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_project_and_environment(
        self, project_id: UUID, environment: str
    ) -> DeploymentConfig | None:
        raise NotImplementedError


class IDeploymentRepository(ABC):
    @abstractmethod
    async def save(self, deployment: Deployment) -> Deployment:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, deployment_id: UUID) -> Deployment | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_config_id(self, config_id: UUID) -> list[Deployment]:
        raise NotImplementedError

    @abstractmethod
    async def get_latest_by_config(self, config_id: UUID) -> Deployment | None:
        raise NotImplementedError


class IAuthService(ABC):
    @abstractmethod
    async def get_current_user_id(self, access_token: str) -> UUID:
        raise NotImplementedError

    @abstractmethod
    async def verify_project_access(self, access_token: str, project_id: UUID) -> bool:
        raise NotImplementedError
