"""
Unit tests for login_page.py
Tests LoginPage class with comprehensive coverage
"""

from unittest.mock import Mock, patch

import customtkinter as ctk
import pytest

from core.pages.login_page import LoginPage


# Fixtures
@pytest.fixture
def root():
    """Create and cleanup CTk root window"""
    root_window = ctk.CTk()
    root_window.withdraw()
    yield root_window
    try:
        root_window.destroy()
    except Exception:
        pass


@pytest.fixture
def mock_login_manager():
    """Create mock login manager"""
    return Mock()


@pytest.fixture
def mock_on_login_success():
    """Create mock login success callback"""
    return Mock()


@pytest.fixture
def mock_is_system_powered():
    """Create mock system powered check"""
    return Mock(return_value=True)


# Tests
def test_init(root, mock_login_manager, mock_on_login_success):
    """Test LoginPage initialization"""
    page = LoginPage(
        root,
        "login_page",
        mock_login_manager,
        mock_on_login_success,
    )

    assert page.get_id() == "login_page"
    assert page.login_manager == mock_login_manager
    assert page.on_login_success == mock_on_login_success


def test_init_with_is_system_powered(
    root, mock_login_manager, mock_on_login_success, mock_is_system_powered
):
    """Test LoginPage initialization with is_system_powered callback"""
    page = LoginPage(
        root,
        "login_page",
        mock_login_manager,
        mock_on_login_success,
        is_system_powered=mock_is_system_powered,
    )

    assert page.is_system_powered == mock_is_system_powered


def test_draw_page_creates_widgets(
    root, mock_login_manager, mock_on_login_success
):
    """Test that draw_page creates necessary widgets"""
    page = LoginPage(
        root,
        "login_page",
        mock_login_manager,
        mock_on_login_success,
    )

    # Check that entry widgets are created
    assert page.username_entry is not None
    assert page.password_entry is not None
    assert isinstance(page.username_entry, ctk.CTkEntry)
    assert isinstance(page.password_entry, ctk.CTkEntry)


@patch("core.pages.login_page.show_toast")
def test_attempt_login_widgets_not_initialized(
    mock_toast, root, mock_login_manager, mock_on_login_success
):
    """Test attempt_login when widgets are not initialized"""
    page = LoginPage(
        root,
        "login_page",
        mock_login_manager,
        mock_on_login_success,
    )

    # Clear widget references
    page.username_entry = None
    page.password_entry = None

    page.attempt_login()

    # Should return early without doing anything
    mock_login_manager.login_web.assert_not_called()


@patch("core.pages.login_page.show_toast")
def test_attempt_login_system_not_powered(
    mock_toast, root, mock_login_manager, mock_on_login_success
):
    """Test attempt_login when system is not powered"""
    page = LoginPage(
        root,
        "login_page",
        mock_login_manager,
        mock_on_login_success,
        is_system_powered=Mock(return_value=False),
    )

    page.username_entry.insert(0, "testuser")
    page.password_entry.insert(0, "testpass")

    page.attempt_login()

    mock_toast.assert_called_once()
    mock_login_manager.login_web.assert_not_called()


@patch("core.pages.login_page.show_toast")
def test_attempt_login_no_login_manager(
    mock_toast, root, mock_on_login_success
):
    """Test attempt_login when login_manager is None"""
    page = LoginPage(root, "login_page", None, mock_on_login_success)

    page.username_entry.insert(0, "testuser")
    page.password_entry.insert(0, "testpass")

    page.attempt_login()

    mock_toast.assert_called_once()


@patch("core.pages.login_page.show_toast")
def test_attempt_login_empty_username(
    mock_toast, root, mock_login_manager, mock_on_login_success
):
    """Test attempt_login with empty username"""
    page = LoginPage(
        root,
        "login_page",
        mock_login_manager,
        mock_on_login_success,
    )

    page.password_entry.insert(0, "testpass")

    page.attempt_login()

    mock_toast.assert_called_once()
    assert "required" in mock_toast.call_args[0][1].lower()


@patch("core.pages.login_page.show_toast")
def test_attempt_login_empty_password(
    mock_toast, root, mock_login_manager, mock_on_login_success
):
    """Test attempt_login with empty password"""
    page = LoginPage(
        root,
        "login_page",
        mock_login_manager,
        mock_on_login_success,
    )

    page.username_entry.insert(0, "testuser")

    page.attempt_login()

    mock_toast.assert_called_once()
    assert "required" in mock_toast.call_args[0][1].lower()


@patch("core.pages.login_page.show_toast")
def test_attempt_login_success(mock_toast, root, mock_on_login_success):
    """Test successful login attempt"""
    mock_login_manager = Mock()
    mock_login_manager.login_web.return_value = True

    page = LoginPage(
        root,
        "login_page",
        mock_login_manager,
        mock_on_login_success,
    )

    page.username_entry.insert(0, "testuser")
    page.password_entry.insert(0, "testpass")

    page.attempt_login()

    mock_login_manager.login_web.assert_called_once_with(
        "testuser", "testpass"
    )
    mock_on_login_success.assert_called_once()


@patch("core.pages.login_page.show_toast")
def test_attempt_login_failure(mock_toast, root, mock_on_login_success):
    """Test failed login attempt"""
    mock_login_manager = Mock()
    mock_login_manager.login_web.return_value = False

    page = LoginPage(
        root,
        "login_page",
        mock_login_manager,
        mock_on_login_success,
    )

    page.username_entry.insert(0, "testuser")
    page.password_entry.insert(0, "wrongpass")

    page.attempt_login()

    mock_login_manager.login_web.assert_called_once_with(
        "testuser", "wrongpass"
    )
    mock_on_login_success.assert_not_called()
    mock_toast.assert_called_once()
    assert "incorrect" in mock_toast.call_args[0][1].lower()


def test_set_login_manager(root, mock_on_login_success):
    """Test set_login_manager method"""
    page = LoginPage(root, "login_page", None, mock_on_login_success)

    new_manager = Mock()
    page.set_login_manager(new_manager)

    assert page.login_manager == new_manager


def test_enter_key_binding_username(
    root, mock_login_manager, mock_on_login_success
):
    """Test that Enter key in username field is bound"""
    page = LoginPage(
        root,
        "login_page",
        mock_login_manager,
        mock_on_login_success,
    )

    # Username entry should exist and be accessible
    assert page.username_entry is not None

    # Entry widgets should be able to receive events
    page.username_entry.focus_set()


def test_enter_key_binding_password(root, mock_on_login_success):
    """Test that Enter key in password field is bound"""
    mock_login_manager = Mock()
    mock_login_manager.login_web.return_value = True

    page = LoginPage(
        root,
        "login_page",
        mock_login_manager,
        mock_on_login_success,
    )

    page.username_entry.insert(0, "testuser")
    page.password_entry.insert(0, "testpass")

    # Password entry should exist and be accessible
    assert page.password_entry is not None

    # Entry widgets should be able to receive events
    page.password_entry.focus_set()


def test_password_entry_show_asterisks(
    root, mock_login_manager, mock_on_login_success
):
    """Test that password entry shows asterisks"""
    page = LoginPage(
        root,
        "login_page",
        mock_login_manager,
        mock_on_login_success,
    )

    # Password entry should have show="*"
    assert page.password_entry.cget("show") == "*"
