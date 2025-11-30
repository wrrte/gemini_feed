import os
import tempfile

import pytest

from manager.login_manager import LoginManager
from manager.storage_manager import StorageManager


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    yield path

    # Cleanup
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def storage_manager(temp_db):
    """Create a StorageManager with temporary database."""
    return StorageManager(db_path=temp_db)


@pytest.fixture
def login_manager(storage_manager):
    """Create a LoginManager with StorageManager."""

    storage_manager.execute_query("DELETE FROM users")

    # Insert test user
    storage_manager.execute_query(
        """
        INSERT INTO users (user_id, role, panel_id, panel_password,
                          web_id, web_password)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("test_user", "HOMEOWNER", "admin", "1234", "webuser", "12345678"),
    )

    return LoginManager(storage_manager=storage_manager)


def test_login_manager_initialization(login_manager):
    """Test LoginManager initialization."""
    assert login_manager.storage_manager is not None
    assert login_manager.login_trials == 0


def test_login_panel_success(login_manager):
    """Test successful panel login."""
    result = login_manager.login_panel("admin", "1234")
    assert result is True
    assert login_manager.login_trials == 0


def test_login_panel_wrong_password(login_manager):
    """Test panel login with wrong password."""
    result = login_manager.login_panel("admin", "wrong")
    assert result is False
    assert login_manager.login_trials == 1


def test_login_panel_wrong_username(login_manager):
    """Test panel login with wrong username."""
    result = login_manager.login_panel("wronguser", "1234")
    assert result is False
    assert login_manager.login_trials == 1


def test_login_panel_both_wrong(login_manager):
    """Test panel login with both username and password wrong."""
    result = login_manager.login_panel("wronguser", "wrong")
    assert result is False
    assert login_manager.login_trials == 1


def test_login_panel_multiple_failures(login_manager):
    """Test multiple failed panel login attempts."""
    # First failure
    result1 = login_manager.login_panel("admin", "wrong1")
    assert result1 is False
    assert login_manager.login_trials == 1

    # Second failure
    result2 = login_manager.login_panel("admin", "wrong2")
    assert result2 is False
    assert login_manager.login_trials == 2

    # Third failure
    result3 = login_manager.login_panel("admin", "wrong3")
    assert result3 is False
    assert login_manager.login_trials == 3


def test_login_panel_reset_trials_on_success(login_manager):
    """Test that login trials reset on successful login."""
    # Failed attempts
    login_manager.login_panel("admin", "wrong1")
    login_manager.login_panel("admin", "wrong2")
    assert login_manager.login_trials == 2

    # Successful login should reset trials
    result = login_manager.login_panel("admin", "1234")
    assert result is True
    assert login_manager.login_trials == 0


def test_login_web_success(login_manager):
    """Test successful web login."""
    result = login_manager.login_web("webuser", "12345678")
    assert result is True
    assert login_manager.login_trials == 0


def test_login_web_wrong_password(login_manager):
    """Test web login with wrong password."""
    result = login_manager.login_web("webuser", "wrong")
    assert result is False
    assert login_manager.login_trials == 1


def test_login_web_wrong_username(login_manager):
    """Test web login with wrong username."""
    result = login_manager.login_web("wronguser", "12345678")
    assert result is False
    assert login_manager.login_trials == 1


def test_login_web_both_wrong(login_manager):
    """Test web login with both username and password wrong."""
    result = login_manager.login_web("wronguser", "wrong")
    assert result is False
    assert login_manager.login_trials == 1


def test_login_web_multiple_failures(login_manager):
    """Test multiple failed web login attempts."""
    # First failure
    result1 = login_manager.login_web("webuser", "wrong1")
    assert result1 is False
    assert login_manager.login_trials == 1

    # Second failure
    result2 = login_manager.login_web("webuser", "wrong2")
    assert result2 is False
    assert login_manager.login_trials == 2

    # Third failure
    result3 = login_manager.login_web("webuser", "wrong3")
    assert result3 is False
    assert login_manager.login_trials == 3


def test_login_web_reset_trials_on_success(login_manager):
    """Test that login trials reset on successful web login."""
    # Failed attempts
    login_manager.login_web("webuser", "wrong1")
    login_manager.login_web("webuser", "wrong2")
    assert login_manager.login_trials == 2

    # Successful login should reset trials
    result = login_manager.login_web("webuser", "12345678")
    assert result is True
    assert login_manager.login_trials == 0


def test_mixed_login_attempts(login_manager):
    """Test mixed panel and web login attempts."""
    # Panel failure
    login_manager.login_panel("admin", "wrong")
    assert login_manager.login_trials == 1

    # Web failure
    login_manager.login_web("webuser", "wrong")
    assert login_manager.login_trials == 2

    # Panel success should reset
    result = login_manager.login_panel("admin", "1234")
    assert result is True
    assert login_manager.login_trials == 0


def test_login_panel_empty_credentials(login_manager):
    """Test panel login with empty credentials."""
    result = login_manager.login_panel("", "")
    assert result is False
    assert login_manager.login_trials == 1


def test_login_web_empty_credentials(login_manager):
    """Test web login with empty credentials."""
    result = login_manager.login_web("", "")
    assert result is False
    assert login_manager.login_trials == 1


def test_login_panel_case_sensitive(login_manager):
    """Test that panel login is case-sensitive."""
    # Uppercase should fail
    result = login_manager.login_panel("ADMIN", "1234")
    assert result is False
    assert login_manager.login_trials == 1


def test_login_web_case_sensitive(login_manager):
    """Test that web login is case-sensitive."""
    # Uppercase should fail
    result = login_manager.login_web("WEBUSER", "12345678")
    assert result is False
    assert login_manager.login_trials == 1


def test_login_manager_with_multiple_users(storage_manager):
    """Test LoginManager with multiple users."""
    # Insert multiple users
    storage_manager.execute_query(
        """
        INSERT INTO users (user_id, role, panel_id, panel_password,
                          web_id, web_password)
        VALUES
        (?, ?, ?, ?, ?, ?),
        (?, ?, ?, ?, ?, ?)
        """,
        (
            "user1",
            "HOMEOWNER",
            "panel1",
            "pass1",
            "web1",
            "webpass1",
            "user2",
            "HOMEOWNER",
            "panel2",
            "pass2",
            "web2",
            "webpass2",
        ),
    )

    login_manager = LoginManager(storage_manager=storage_manager)

    # Login with first user
    assert login_manager.login_panel("panel1", "pass1") is True
    assert login_manager.login_trials == 0

    # Login with second user
    assert login_manager.login_web("web2", "webpass2") is True
    assert login_manager.login_trials == 0

    # Wrong user credentials
    assert login_manager.login_panel("panel1", "pass2") is False
    assert login_manager.login_trials == 1
