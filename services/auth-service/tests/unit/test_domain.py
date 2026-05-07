import uuid
from datetime import UTC, datetime

import pytest

from auth_service.domain.entities import TokenPair, User, UserRole


def make_user(**kwargs):
    now = datetime.now(UTC)
    defaults = dict(
        id=uuid.uuid4(),
        email="u@example.com",
        username="u",
        role=UserRole.USER,
        created_at=now,
        updated_at=now,
    )
    defaults.update(kwargs)
    return User(**defaults)


class TestTokenPair:
    def test_valid_creation(self):
        pair = TokenPair(access_token="acc", refresh_token="ref", expires_in=900)
        assert pair.token_type == "bearer"

    def test_empty_access_token_raises(self):
        with pytest.raises(ValueError, match="Tokens cannot be empty"):
            TokenPair(access_token="", refresh_token="ref", expires_in=900)

    def test_empty_refresh_token_raises(self):
        with pytest.raises(ValueError, match="Tokens cannot be empty"):
            TokenPair(access_token="acc", refresh_token="", expires_in=900)

    def test_zero_expires_in_raises(self):
        with pytest.raises(ValueError, match="expires_in must be positive"):
            TokenPair(access_token="acc", refresh_token="ref", expires_in=0)

    def test_negative_expires_in_raises(self):
        with pytest.raises(ValueError, match="expires_in must be positive"):
            TokenPair(access_token="acc", refresh_token="ref", expires_in=-1)


class TestUserEntity:
    def test_update_last_login_sets_timestamp(self):
        user = make_user()
        assert user.last_login_at is None

        user.update_last_login()

        assert user.last_login_at is not None
        assert user.updated_at is not None

    def test_update_last_login_updates_updated_at(self):
        old_time = datetime(2020, 1, 1, tzinfo=UTC)
        user = make_user(updated_at=old_time)

        user.update_last_login()

        assert user.updated_at > old_time

    def test_user_role_enum_values(self):
        assert UserRole.USER == "user"
        assert UserRole.ADMIN == "admin"
        assert UserRole.MODERATOR == "moderator"

    def test_user_default_role(self):
        user = make_user(role=UserRole.USER)
        assert user.role == UserRole.USER
