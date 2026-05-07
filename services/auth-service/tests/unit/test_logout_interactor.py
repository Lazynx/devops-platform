import pytest

from auth_service.application.dtos import LogoutInputDTO
from auth_service.application.interactors.logout import LogoutInteractor


@pytest.mark.anyio
async def test_logout_deletes_session(jwt_service, test_user, test_session, session_id, mock_session_repo):
    token = jwt_service.create_access_token(test_user, session_id)
    mock_session_repo.get_by_id.return_value = test_session

    interactor = LogoutInteractor(mock_session_repo, jwt_service)
    await interactor(LogoutInputDTO(token=token))

    mock_session_repo.delete.assert_called_once_with(session_id)


@pytest.mark.anyio
async def test_logout_already_expired_session_is_silent(jwt_service, test_user, session_id, mock_session_repo):
    token = jwt_service.create_access_token(test_user, session_id)
    mock_session_repo.get_by_id.return_value = None

    interactor = LogoutInteractor(mock_session_repo, jwt_service)
    await interactor(LogoutInputDTO(token=token))

    mock_session_repo.delete.assert_not_called()


@pytest.mark.anyio
async def test_logout_invalid_token_raises(jwt_service, mock_session_repo):
    interactor = LogoutInteractor(mock_session_repo, jwt_service)

    with pytest.raises(ValueError):
        await interactor(LogoutInputDTO(token="bad.token"))
