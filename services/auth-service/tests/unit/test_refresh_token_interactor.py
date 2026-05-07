import uuid
from datetime import UTC, datetime

import pytest

from auth_service.application.dtos import RefreshTokenInputDTO
from auth_service.application.interactors.refresh_token import RefreshTokenInteractor
from auth_service.domain.entities import SessionData


@pytest.mark.anyio
async def test_refresh_success_returns_new_token_pair(
    jwt_service, test_user, test_session, session_id, mock_user_repo, mock_session_repo
):
    refresh_token = jwt_service.create_refresh_token(test_user.id, session_id)
    mock_session_repo.get_by_id.return_value = test_session
    mock_user_repo.get_by_id.return_value = test_user
    mock_session_repo.update.return_value = test_session

    interactor = RefreshTokenInteractor(mock_user_repo, mock_session_repo, jwt_service)
    result = await interactor(RefreshTokenInputDTO(refresh_token=refresh_token))

    assert result.access_token
    assert result.refresh_token
    assert result.user_id == test_user.id
    assert result.email == test_user.email


@pytest.mark.anyio
async def test_refresh_invalid_token_raises(jwt_service, mock_user_repo, mock_session_repo):
    interactor = RefreshTokenInteractor(mock_user_repo, mock_session_repo, jwt_service)

    with pytest.raises(ValueError, match="Invalid or expired refresh token"):
        await interactor(RefreshTokenInputDTO(refresh_token="invalid.token"))


@pytest.mark.anyio
async def test_refresh_session_not_found_raises(jwt_service, test_user, session_id, mock_user_repo, mock_session_repo):
    refresh_token = jwt_service.create_refresh_token(test_user.id, session_id)
    mock_session_repo.get_by_id.return_value = None

    interactor = RefreshTokenInteractor(mock_user_repo, mock_session_repo, jwt_service)

    with pytest.raises(ValueError, match="Session not found or expired"):
        await interactor(RefreshTokenInputDTO(refresh_token=refresh_token))


@pytest.mark.anyio
async def test_refresh_session_user_mismatch_raises(
    jwt_service, test_user, session_id, mock_user_repo, mock_session_repo
):
    refresh_token = jwt_service.create_refresh_token(test_user.id, session_id)

    now = datetime.now(UTC)
    wrong_user_id = uuid.uuid4()
    mismatched_session = SessionData(
        id=session_id,
        user_id=wrong_user_id,
        device_info=None,
        ip_address=None,
        created_at=now,
        last_activity=now,
        expires_at=now,
    )
    mock_session_repo.get_by_id.return_value = mismatched_session

    interactor = RefreshTokenInteractor(mock_user_repo, mock_session_repo, jwt_service)

    with pytest.raises(ValueError, match="Session does not belong to user"):
        await interactor(RefreshTokenInputDTO(refresh_token=refresh_token))


@pytest.mark.anyio
async def test_refresh_user_not_found_raises(
    jwt_service, test_user, test_session, session_id, mock_user_repo, mock_session_repo
):
    refresh_token = jwt_service.create_refresh_token(test_user.id, session_id)
    mock_session_repo.get_by_id.return_value = test_session
    mock_user_repo.get_by_id.return_value = None

    interactor = RefreshTokenInteractor(mock_user_repo, mock_session_repo, jwt_service)

    with pytest.raises(ValueError, match="User not found"):
        await interactor(RefreshTokenInputDTO(refresh_token=refresh_token))
