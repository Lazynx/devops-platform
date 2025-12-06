from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum as PyEnum
from uuid import UUID, uuid4


class UserRole(str, PyEnum):
    USER = 'user'
    ADMIN = 'admin'
    MODERATOR = 'moderator'


class OAuthProvider(str, PyEnum):
    GITHUB = 'github'
    GITLAB = 'gitlab'


@dataclass
class User:
    email: str
    username: str
    id: UUID = field(default_factory=uuid4)
    avatar_url: str | None = None
    role: UserRole = UserRole.USER
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_login_at: datetime | None = None

    def update_last_login(self) -> None:
        self.last_login_at = datetime.now()


@dataclass
class OAuthConnection:
    user_id: UUID
    provider: OAuthProvider
    provider_user_id: str
    access_token: str
    id: UUID = field(default_factory=uuid4)
    refresh_token: str | None = None
    token_expires_at: datetime | None = None
    scopes: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass(slots=True)
class SessionData:
    id: UUID
    user_id: UUID
    device_info: str | None
    ip_address: str | None
    created_at: datetime
    last_activity: datetime
    expires_at: datetime


@dataclass(slots=True)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = 'bearer'

    def __post_init__(self):
        if not self.access_token or not self.refresh_token:
            raise ValueError('Tokens cannot be empty')
        if self.expires_in <= 0:
            raise ValueError('expires_in must be positive')