from uuid import UUID

from auth_service.application.dtos import LogoutInputDTO
from auth_service.application.interfaces import ISessionRepository
from auth_service.infrastructure.security.jwt_service import JWTService


class LogoutInteractor:
    def __init__(
        self,
        session_repository: ISessionRepository,
        jwt_service: JWTService,
    ):
        self._session_repo = session_repository
        self._jwt_service = jwt_service

    async def __call__(self, dto: LogoutInputDTO) -> None:
        payload = self._jwt_service.verify_access_token(dto.token)
        session_id = UUID(payload.session_id)

        session = await self._session_repo.get_by_id(session_id)
        if not session:
            return

        await self._session_repo.delete(session_id)
