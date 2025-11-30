"""
Unit tests for view_log_page.py
Tests ViewLogPage class
"""

from unittest.mock import Mock, patch

import customtkinter as ctk
import pytest

from core.pages.view_log_page import ViewLogPage


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
def mock_log_manager():
    """Create mock log manager"""
    manager = Mock()
    manager.get_logs.return_value = [
        "[INFO] Test log 1\n",
        "[ERROR] Test log 2\n",
        "[DEBUG] Test log 3\n",
    ]
    return manager


# Tests for initialization
@patch("core.pages.view_log_page.LogManager")
def test_init_default(mock_log_manager_class, root):
    """Test ViewLogPage initialization with default parameters"""
    mock_log_manager_class.return_value = Mock()

    page = ViewLogPage(root, "view_log")

    assert page.get_id() == "view_log"
    assert page.current_filter == "ALL"
    assert page.log_manager is not None


@patch("core.pages.view_log_page.LogManager")
def test_init_custom_title(mock_log_manager_class, root):
    """Test ViewLogPage initialization with custom title"""
    mock_log_manager_class.return_value = Mock()

    page = ViewLogPage(root, "view_log", title="Custom Log Viewer")

    assert page.title() == "Custom Log Viewer"


# Tests for draw_page
@patch("core.pages.view_log_page.LogManager")
def test_draw_page_creates_widgets(mock_log_manager_class, root):
    """Test that draw_page creates necessary widgets"""
    mock_log_manager_class.return_value = Mock()

    page = ViewLogPage(root, "view_log")

    assert page.log_textbox is not None
    assert page.log_count_label is not None
    assert isinstance(page.log_textbox, ctk.CTkTextbox)


# Tests for refresh_logs
@patch("core.pages.view_log_page.LogManager")
def test_refresh_logs_success(mock_log_manager_class, root):
    """Test successful log refresh"""
    mock_manager = Mock()
    mock_manager.get_logs.return_value = [
        "[INFO] Test log 1\n",
        "[ERROR] Test log 2\n",
    ]
    mock_log_manager_class.return_value = mock_manager

    page = ViewLogPage(root, "view_log")
    page.refresh_logs()

    mock_manager.get_logs.assert_called()
    assert "Total: 2 logs" in page.log_count_label.cget("text")


@patch("core.pages.view_log_page.LogManager")
def test_refresh_logs_empty(mock_log_manager_class, root):
    """Test log refresh with no logs"""
    mock_manager = Mock()
    mock_manager.get_logs.return_value = []
    mock_log_manager_class.return_value = mock_manager

    page = ViewLogPage(root, "view_log")
    page.refresh_logs()

    assert "Total: 0 logs" in page.log_count_label.cget("text")


@patch("core.pages.view_log_page.LogManager")
def test_refresh_logs_error(mock_log_manager_class, root):
    """Test log refresh with error"""
    mock_manager = Mock()
    mock_manager.get_logs.side_effect = Exception("Test error")
    mock_log_manager_class.return_value = mock_manager

    page = ViewLogPage(root, "view_log")
    page.refresh_logs()

    # Should handle error gracefully
    assert page.log_textbox is not None


# Tests for filter_logs
@patch("core.pages.view_log_page.LogManager")
def test_filter_logs_all(mock_log_manager_class, root):
    """Test filtering logs with ALL filter"""
    mock_manager = Mock()
    mock_manager.get_logs.return_value = [
        "[INFO] Test log 1\n",
        "[ERROR] Test log 2\n",
    ]
    mock_log_manager_class.return_value = mock_manager

    page = ViewLogPage(root, "view_log")
    page.filter_logs("ALL")

    assert page.current_filter == "ALL"


@patch("core.pages.view_log_page.LogManager")
def test_filter_logs_specific_level(mock_log_manager_class, root):
    """Test filtering logs by specific level"""
    mock_manager = Mock()
    mock_manager.get_logs.return_value = [
        "[INFO] Test log 1\n",
        "[ERROR] Test log 2\n",
        "[DEBUG] Test log 3\n",
    ]
    mock_log_manager_class.return_value = mock_manager

    page = ViewLogPage(root, "view_log")
    page.filter_logs("ERROR")

    assert page.current_filter == "ERROR"


@patch("core.pages.view_log_page.LogManager")
def test_filter_logs_info(mock_log_manager_class, root):
    """Test filtering INFO logs"""
    mock_manager = Mock()
    mock_manager.get_logs.return_value = [
        "[INFO] Test log 1\n",
        "[ERROR] Test log 2\n",
    ]
    mock_log_manager_class.return_value = mock_manager

    page = ViewLogPage(root, "view_log")
    page.filter_logs("INFO")

    assert page.current_filter == "INFO"


@patch("core.pages.view_log_page.LogManager")
def test_filter_logs_warning(mock_log_manager_class, root):
    """Test filtering WARNING logs"""
    mock_manager = Mock()
    mock_manager.get_logs.return_value = [
        "[WARNING] Test log 1\n",
        "[ERROR] Test log 2\n",
    ]
    mock_log_manager_class.return_value = mock_manager

    page = ViewLogPage(root, "view_log")
    page.filter_logs("WARNING")

    assert page.current_filter == "WARNING"


@patch("core.pages.view_log_page.LogManager")
def test_filter_logs_critical(mock_log_manager_class, root):
    """Test filtering CRITICAL logs"""
    mock_manager = Mock()
    mock_manager.get_logs.return_value = [
        "[CRITICAL] Test log 1\n",
        "[ERROR] Test log 2\n",
    ]
    mock_log_manager_class.return_value = mock_manager

    page = ViewLogPage(root, "view_log")
    page.filter_logs("CRITICAL")

    assert page.current_filter == "CRITICAL"


@patch("core.pages.view_log_page.LogManager")
def test_filter_logs_debug(mock_log_manager_class, root):
    """Test filtering DEBUG logs"""
    mock_manager = Mock()
    mock_manager.get_logs.return_value = [
        "[DEBUG] Test log 1\n",
        "[ERROR] Test log 2\n",
    ]
    mock_log_manager_class.return_value = mock_manager

    page = ViewLogPage(root, "view_log")
    page.filter_logs("DEBUG")

    assert page.current_filter == "DEBUG"


# Tests for clear_display
@patch("core.pages.view_log_page.LogManager")
def test_clear_display(mock_log_manager_class, root):
    """Test clearing log display"""
    mock_log_manager_class.return_value = Mock()

    page = ViewLogPage(root, "view_log")
    page.clear_display()

    assert "Total: 0 logs" in page.log_count_label.cget("text")


# Tests for _filter_log_lines
@patch("core.pages.view_log_page.LogManager")
def test_filter_log_lines_all(mock_log_manager_class, root):
    """Test _filter_log_lines with ALL filter"""
    mock_log_manager_class.return_value = Mock()

    page = ViewLogPage(root, "view_log")
    page.current_filter = "ALL"

    logs = ["[INFO] Log 1\n", "[ERROR] Log 2\n"]
    result = page._filter_log_lines(logs)

    assert len(result) == 2


@patch("core.pages.view_log_page.LogManager")
def test_filter_log_lines_specific(mock_log_manager_class, root):
    """Test _filter_log_lines with specific filter"""
    mock_log_manager_class.return_value = Mock()

    page = ViewLogPage(root, "view_log")
    page.current_filter = "ERROR"

    logs = ["[INFO] Log 1\n", "[ERROR] Log 2\n", "[ERROR] Log 3\n"]
    result = page._filter_log_lines(logs)

    assert len(result) == 2
    assert all("[ERROR]" in log for log in result)


# Tests for _insert_colored_log
@patch("core.pages.view_log_page.LogManager")
def test_insert_colored_log(mock_log_manager_class, root):
    """Test _insert_colored_log inserts log"""
    mock_log_manager_class.return_value = Mock()

    page = ViewLogPage(root, "view_log")
    page._insert_colored_log("[INFO] Test log\n")

    # Should not throw error
    assert page.log_textbox is not None


# Tests for _darken_color
@patch("core.pages.view_log_page.LogManager")
def test_darken_color_valid(mock_log_manager_class, root):
    """Test _darken_color with valid hex color"""
    mock_log_manager_class.return_value = Mock()

    page = ViewLogPage(root, "view_log")
    result = page._darken_color("#ff0000")

    assert result.startswith("#")
    assert len(result) == 7


@patch("core.pages.view_log_page.LogManager")
def test_darken_color_invalid(mock_log_manager_class, root):
    """Test _darken_color with invalid color"""
    mock_log_manager_class.return_value = Mock()

    page = ViewLogPage(root, "view_log")
    result = page._darken_color("invalid")

    assert result == "invalid"


@patch("core.pages.view_log_page.LogManager")
def test_darken_color_with_hash(mock_log_manager_class, root):
    """Test _darken_color removes hash and processes"""
    mock_log_manager_class.return_value = Mock()

    page = ViewLogPage(root, "view_log")
    result = page._darken_color("#aabbcc")

    assert result.startswith("#")


@patch("core.pages.view_log_page.LogManager")
def test_darken_color_calculation(mock_log_manager_class, root):
    """Test _darken_color produces darker color"""
    mock_log_manager_class.return_value = Mock()

    page = ViewLogPage(root, "view_log")
    original = "#ffffff"  # white
    result = page._darken_color(original)

    # Result should be darker (smaller hex values)
    assert result != original
    assert result < original  # String comparison works for hex
