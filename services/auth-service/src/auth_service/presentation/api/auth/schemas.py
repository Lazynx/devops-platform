from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from auth_service.application.dtos import LoginResultDTO, UserResponseOutputDTO
from auth_service.domain.entities import UserRole


class UserBase(BaseModel):
    email: str
    username: str | None = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    role: UserRole
    avatar_url: str | None = None
    created_at: datetime
    last_login_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_dto(cls, dto: UserResponseOutputDTO) -> 'UserResponse':
        return cls(
            id=dto.id,
            email=dto.email,
            username=dto.username,
            role=dto.role,
            avatar_url=dto.avatar_url,
            created_at=dto.created_at,
            last_login_at=dto.last_login_at,
        )


class GitHubAuthUrlResponse(BaseModel):
    authorization_url: str


class GitHubCallbackRequest(BaseModel):
    code: str
    device_info: str | None = None
    ip_address: str | None = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

    @classmethod
    def from_dto(cls, dto: LoginResultDTO) -> 'RefreshTokenResponse':
        return cls(
            access_token=dto.access_token,
            token_type='Bearer',
            expires_in=dto.expires_in,
        )


class LogoutRequest(BaseModel):
    token: str


class LogoutResponse(BaseModel):
    message: str


class GitHubTokenResponse(BaseModel):
    github_token: str


class OAuthUserInfo(BaseModel):
    oauth_id: str
    email: str
    username: str | None
    avatar_url: str | None = None
