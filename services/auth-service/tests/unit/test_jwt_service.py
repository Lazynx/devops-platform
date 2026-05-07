import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from pydantic import SecretStr

from auth_service.domain.entities import User, UserRole
from auth_service.infrastructure.security.jwt_service import JWTService


def make_user(user_id=None):
    now = datetime.now(UTC)
    return User(
        id=user_id or uuid.uuid4(),
        email="user@example.com",
        username="user",
        role=UserRole.USER,
        created_at=now,
        updated_at=now,
    )


def make_jwt_service(**kwargs):
    defaults = dict(
        secret_key=SecretStr("secret"),
        algorithm="HS256",
        access_token_expire_minutes=15,
        refresh_token_expire_days=30,
    )
    defaults.update(kwargs)
    return JWTService(**defaults)


def test_create_access_token_returns_string(jwt_service, test_user, session_id):
    token = jwt_service.create_access_token(test_user, session_id)
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_refresh_token_returns_string(jwt_service, user_id, session_id):
    token = jwt_service.create_refresh_token(user_id, session_id)
    assert isinstance(token, str)
    assert len(token) > 0


def test_verify_access_token_returns_correct_payload(jwt_service, test_user, session_id):
    token = jwt_service.create_access_token(test_user, session_id)
    payload = jwt_service.verify_access_token(token)

    assert payload.sub == str(test_user.id)
    assert payload.session_id == str(session_id)
    assert payload.role == test_user.role


def test_verify_refresh_token_returns_correct_payload(jwt_service, test_user, session_id):
    token = jwt_service.create_refresh_token(test_user.id, session_id)
    payload = jwt_service.verify_refresh_token(token)

    assert payload.sub == str(test_user.id)
    assert payload.session_id == str(session_id)


def test_verify_access_token_invalid_raises(jwt_service):
    with pytest.raises(ValueError, match="Invalid access token"):
        jwt_service.verify_access_token("not.a.valid.token")


def test_verify_refresh_token_invalid_raises(jwt_service):
    with pytest.raises(ValueError, match="Invalid refresh token"):
        jwt_service.verify_refresh_token("garbage")


def test_verify_access_token_wrong_secret_raises(test_user, session_id):
    svc1 = make_jwt_service(secret_key=SecretStr("secret-a"))
    svc2 = make_jwt_service(secret_key=SecretStr("secret-b"))

    token = svc1.create_access_token(test_user, session_id)

    with pytest.raises(ValueError):
        svc2.verify_access_token(token)


def test_create_token_pair_expires_in_matches_config(test_user, session_id):
    svc = make_jwt_service(access_token_expire_minutes=5)
    pair = svc.create_token_pair(test_user, session_id)

    assert pair.expires_in == 5 * 60
    assert pair.token_type == "bearer"


def test_create_token_pair_both_tokens_verifiable(jwt_service, test_user, session_id):
    pair = jwt_service.create_token_pair(test_user, session_id)

    access_payload = jwt_service.verify_access_token(pair.access_token)
    refresh_payload = jwt_service.verify_refresh_token(pair.refresh_token)

    assert access_payload.sub == str(test_user.id)
    assert refresh_payload.sub == str(test_user.id)
    assert access_payload.session_id == refresh_payload.session_id


def test_access_token_expiry_is_in_future(jwt_service, test_user, session_id):
    token = jwt_service.create_access_token(test_user, session_id)
    payload = jwt.decode(token, "secret", algorithms=["HS256"], options={"verify_signature": False})
    assert payload["exp"] > int(datetime.now(UTC).timestamp())


def test_access_token_with_admin_role(session_id):
    now = datetime.now(UTC)
    admin = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        username="admin",
        role=UserRole.ADMIN,
        created_at=now,
        updated_at=now,
    )
    svc = make_jwt_service()
    token = svc.create_access_token(admin, session_id)
    payload = svc.verify_access_token(token)

    assert payload.role == UserRole.ADMIN
