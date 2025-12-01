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

# 1. change_web_password 관련 테스트 (전체 누락됨)
def test_change_web_password_success(login_manager, mock_storage_manager):
    # 1. 기존 비밀번호 확인 성공, 2. 업데이트 성공
    mock_storage_manager.execute_query.side_effect = [
        [{"user_id": "u1"}],  # _verify_web_password 성공
        True                  # 업데이트 성공
    ]
    # WEB_PASSWORD_LENGTH가 8자리여야 함
    assert login_manager.change_web_password("user1", "old_pass", "12345678") is True

def test_change_web_password_fail_verification(login_manager, mock_storage_manager):
    # 기존 비밀번호 불일치 (빈 리스트 반환)
    mock_storage_manager.execute_query.return_value = [] 
    assert login_manager.change_web_password("user1", "wrong_pass", "12345678") is False

def test_change_web_password_fail_validation(login_manager, mock_storage_manager):
    mock_storage_manager.execute_query.return_value = [{"user_id": "u1"}]
    # 새 비밀번호 길이가 8자리가 아님 (검증 실패)
    assert login_manager.change_web_password("user1", "old_pass", "short") is False

# 2. 예외 처리(Exception) 테스트 (try-except 구문 커버)
def test_change_panel_password_exception(login_manager, mock_storage_manager):
    # 검증은 통과했으나 업데이트 중 DB 에러 발생
    mock_storage_manager.execute_query.side_effect = [
        [{"user_id": "panel1"}], 
        Exception("DB Error")
    ]
    assert login_manager.change_panel_password("1234", "old", "5678") is False

def test_change_web_password_exception(login_manager, mock_storage_manager):
    mock_storage_manager.execute_query.side_effect = [
        [{"user_id": "user1"}], 
        Exception("DB Error")
    ]
    assert login_manager.change_web_password("user1", "old_pass", "12345678") is False

# 3. 패스워드가 None인 경우 테스트 (_verify_panel_password 분기 커버)
def test_login_panel_guest_no_password(login_manager, mock_storage_manager):
    # password가 None일 때의 쿼리 실행 확인
    mock_storage_manager.execute_query.return_value = [{"user_id": "guest"}]
    assert login_manager.login_panel("guest_id", None) is True
    
    # 호출된 쿼리가 'IS NULL'을 포함하는지 확인하여 분기 검증
    args, _ = mock_storage_manager.execute_query.call_args
    assert "IS NULL" in args[0]

# 4. 입력값 유효성 검사 엣지 케이스 (_validate 메서드의 타입 체크 커버)
def test_validate_password_invalid_type(login_manager):
    # _validate_web_password와 _validate_panel_password의 타입 체크(str 여부) 검증
    # change 메서드를 통해 간접 호출하거나 protected 메서드를 직접 테스트 가능
    
    # None 입력
    assert login_manager.change_panel_password("id", "old", None) is False
    assert login_manager.change_web_password("id", "old", None) is False
    
    # 숫자가 아닌 타입 입력 (int 등)
    assert login_manager.change_panel_password("id", "old", 1234) is False
    assert login_manager.change_web_password("id", "old", 12345678) is False