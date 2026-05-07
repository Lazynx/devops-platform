import pytest

from auth_service.application.dtos import GetUserInputDTO
from auth_service.application.interactors.get_user import GetUserInteractor


@pytest.mark.anyio
async def test_get_user_success(jwt_service, test_user, test_session, session_id, mock_user_repo, mock_session_repo):
    token = jwt_service.create_access_token(test_user, session_id)
    mock_session_repo.get_by_id.return_value = test_session
    mock_user_repo.get_by_id.return_value = test_user

    interactor = GetUserInteractor(jwt_service, mock_user_repo, mock_session_repo)
    result = await interactor(GetUserInputDTO(token=token))

    assert result.id == test_user.id
    assert result.email == test_user.email
    assert result.username == test_user.username


@pytest.mark.anyio
async def test_get_user_invalid_token_raises(jwt_service, mock_user_repo, mock_session_repo):
    interactor = GetUserInteractor(jwt_service, mock_user_repo, mock_session_repo)

    with pytest.raises(ValueError):
        await interactor(GetUserInputDTO(token="invalid.token.here"))


@pytest.mark.anyio
async def test_get_user_session_not_found_raises(jwt_service, test_user, session_id, mock_user_repo, mock_session_repo):
    token = jwt_service.create_access_token(test_user, session_id)
    mock_session_repo.get_by_id.return_value = None

    interactor = GetUserInteractor(jwt_service, mock_user_repo, mock_session_repo)

    with pytest.raises(ValueError, match="Session expired or invalid"):
        await interactor(GetUserInputDTO(token=token))


@pytest.mark.anyio
async def test_get_user_user_not_found_raises(jwt_service, test_user, test_session, session_id, mock_user_repo, mock_session_repo):
    token = jwt_service.create_access_token(test_user, session_id)
    mock_session_repo.get_by_id.return_value = test_session
    mock_user_repo.get_by_id.return_value = None

    interactor = GetUserInteractor(jwt_service, mock_user_repo, mock_session_repo)

    with pytest.raises(ValueError, match="User not found"):
        await interactor(GetUserInputDTO(token=token))
