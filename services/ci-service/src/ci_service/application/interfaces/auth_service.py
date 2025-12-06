from abc import ABC, abstractmethod
from uuid import UUID


class IAuthService(ABC):
    @abstractmethod
    async def get_current_user_id(self, user_access_token: str) -> UUID:
        raise NotImplementedError

    @abstractmethod
    async def get_github_token(self, user_access_token: str) -> str:
        raise NotImplementedError

