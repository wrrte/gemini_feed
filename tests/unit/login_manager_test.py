import pytest
from unittest.mock import Mock
from manager.login_manager import LoginManager
from manager.storage_manager import StorageManager
from constants import MAX_LOGIN_TRIALS

@pytest.fixture
def mock_storage_manager():
    return Mock(spec=StorageManager)

@pytest.fixture
def login_manager(mock_storage_manager):
    return LoginManager(storage_manager=mock_storage_manager)

def test_login_panel_success(login_manager, mock_storage_manager):
    mock_storage_manager.execute_query.return_value = [{"user_id": "u1"}]
    assert login_manager.login_panel("1234", "pass") is True
    assert login_manager.is_logged_in_panel is True
    assert login_manager.login_trials == 0

def test_login_panel_fail(login_manager, mock_storage_manager):
    mock_storage_manager.execute_query.return_value = [] # Empty result
    assert login_manager.login_panel("1234", "wrong") is False
    assert login_manager.is_logged_in_panel is False
    assert login_manager.login_trials == 1

def test_login_web_success(login_manager, mock_storage_manager):
    mock_storage_manager.execute_query.return_value = [{"user_id": "u1"}]
    assert login_manager.login_web("user", "password") is True
    assert login_manager.is_logged_in_web is True

def test_logout(login_manager):
    login_manager.is_logged_in_web = True
    login_manager.is_logged_in_panel = True
    
    login_manager.logout_web()
    assert login_manager.is_logged_in_web is False
    
    login_manager.logout_panel()
    assert login_manager.is_logged_in_panel is False

def test_change_panel_password_success(login_manager, mock_storage_manager):
    # Verify old password returns result
    mock_storage_manager.execute_query.side_effect = [
        [{"user_id": "u1"}], # Verify old
        True # Update result (anything not None)
    ]
    
    # 4 digit number required by constant default? Assuming 4 digits based on code.
    # Note: constants imported in code.
    
    assert login_manager.change_panel_password("1234", "old", "5678") is True

def test_change_panel_password_fail_verification(login_manager, mock_storage_manager):
    mock_storage_manager.execute_query.return_value = []
    assert login_manager.change_panel_password("1234", "wrong", "5678") is False

def test_change_panel_password_fail_validation(login_manager, mock_storage_manager):
    mock_storage_manager.execute_query.return_value = [{"user_id": "u1"}]
    # "abc" is not digits
    assert login_manager.change_panel_password("1234", "old", "abc") is False

def test_is_login_trials_exceeded(login_manager):
    login_manager.login_trials = MAX_LOGIN_TRIALS
    assert login_manager.is_login_trials_exceeded() is True
    
    login_manager.login_trials = 0
    assert login_manager.is_login_trials_exceeded() is False