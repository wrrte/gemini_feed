from unittest.mock import Mock

import pytest

from constants import MAX_LOGIN_TRIALS
from manager.login_manager import LoginManager
from manager.storage_manager import StorageManager


@pytest.fixture
def mock_storage_manager():
    return Mock(spec=StorageManager)


@pytest.fixture
def login_manager(mock_storage_manager):
    return LoginManager(storage_manager=mock_storage_manager)


def test_login_panel(login_manager, mock_storage_manager):
    # Success
    mock_storage_manager.execute_query.return_value = [{"user_id": "u1"}]
    assert login_manager.login_panel("1234", "pass") is True
    assert login_manager.is_logged_in_panel is True

    # Fail
    mock_storage_manager.execute_query.return_value = []
    assert login_manager.login_panel("1234", "wrong") is False
    assert login_manager.login_trials == 1


def test_login_web(login_manager, mock_storage_manager):
    mock_storage_manager.execute_query.return_value = [{"user_id": "u1"}]
    assert login_manager.login_web("user", "password") is True
    assert login_manager.is_logged_in_web is True

    mock_storage_manager.execute_query.return_value = []
    assert login_manager.login_web("user", "wrong") is False


def test_logout(login_manager):
    login_manager.is_logged_in_web = True
    login_manager.is_logged_in_panel = True
    login_manager.logout_web()
    assert login_manager.is_logged_in_web is False
    login_manager.logout_panel()
    assert login_manager.is_logged_in_panel is False


def test_change_panel_password(login_manager, mock_storage_manager):
    # Success
    mock_storage_manager.execute_query.side_effect = [[{"u": "u"}], True]
    assert login_manager.change_panel_password("1", "old", "5678") is True

    # Old password incorrect
    mock_storage_manager.execute_query.side_effect = None
    mock_storage_manager.execute_query.return_value = []
    assert login_manager.change_panel_password("1", "wrong", "5678") is False

    # New password invalid (not digit)
    mock_storage_manager.execute_query.return_value = [{"u": "u"}]
    assert login_manager.change_panel_password("1", "old", "abcd") is False

    # DB Exception
    mock_storage_manager.execute_query.side_effect = [
        [{"u": "u"}], Exception("DB Error")]
    assert login_manager.change_panel_password("1", "old", "5678") is False


def test_change_web_password(login_manager, mock_storage_manager):
    # Success
    mock_storage_manager.execute_query.side_effect = [[{"u": "u"}], True]
    assert login_manager.change_web_password("u", "old", "12345678") is True

    # Old password incorrect
    mock_storage_manager.execute_query.side_effect = None
    mock_storage_manager.execute_query.return_value = []
    assert login_manager.change_web_password("u", "wrong", "12345678") is False

    # New password invalid (short)
    mock_storage_manager.execute_query.return_value = [{"u": "u"}]
    assert login_manager.change_web_password("u", "old", "short") is False

    # DB Exception
    mock_storage_manager.execute_query.side_effect = [
        [{"u": "u"}], Exception("DB Error")]
    assert login_manager.change_web_password("u", "old", "12345678") is False


def test_is_login_trials_exceeded(login_manager):
    login_manager.login_trials = MAX_LOGIN_TRIALS
    assert login_manager.is_login_trials_exceeded() is True
    login_manager.login_trials = 0
    assert login_manager.is_login_trials_exceeded() is False


def test_login_panel_guest(login_manager, mock_storage_manager):
    mock_storage_manager.execute_query.return_value = [{"user_id": "guest"}]
    assert login_manager.login_panel("guest", None) is True
    args, _ = mock_storage_manager.execute_query.call_args
    assert "IS NULL" in args[0]


def test_validate_password_edge_cases(login_manager):
    # Panel Password
    assert login_manager.change_panel_password("1", "old", None) is False
    assert login_manager.change_panel_password("1", "old", 1234) is False
    assert login_manager.change_panel_password("1", "old", "") is False

    # Web Password
    assert login_manager.change_web_password("1", "old", None) is False
    assert login_manager.change_web_password("1", "old", 12345678) is False
    assert login_manager.change_web_password("1", "old", "") is False