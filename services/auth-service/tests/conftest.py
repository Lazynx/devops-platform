import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from pydantic import SecretStr


@pytest.fixture
def anyio_backend():
    return "asyncio"

from auth_service.domain.entities import SessionData, User, UserRole
from auth_service.infrastructure.security.jwt_service import JWTService


@pytest.fixture
def jwt_service():
    return JWTService(
        secret_key=SecretStr("test-secret-key-for-testing-only"),
        algorithm="HS256",
        access_token_expire_minutes=15,
        refresh_token_expire_days=30,
    )


@pytest.fixture
def user_id():
    return uuid.uuid4()


@pytest.fixture
def session_id():
    return uuid.uuid4()


@pytest.fixture
def test_user(user_id):
    now = datetime.now(UTC)
    return User(
        id=user_id,
        email="test@example.com",
        username="testuser",
        role=UserRole.USER,
        created_at=now,
        updated_at=now,
        last_login_at=None,
    )


@pytest.fixture
def test_session(session_id, user_id):
    now = datetime.now(UTC)
    return SessionData(
        id=session_id,
        user_id=user_id,
        device_info="Mozilla/5.0",
        ip_address="127.0.0.1",
        created_at=now,
        last_activity=now,
        expires_at=now + timedelta(days=30),
    )


@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def mock_session_repo():
    return AsyncMock()
