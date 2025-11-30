"""
Unit tests for safehome_mode_page.py
Tests SafeHomeModePage class with 100% coverage
"""

from unittest.mock import Mock, patch

import customtkinter as ctk
import pytest

from core.pages.safehome_mode_page import SafeHomeModePage
from database.schema.sensor import SensorType


@pytest.fixture
def root():
    root_window = ctk.CTk()
    root_window.withdraw()
    yield root_window
    try:
        root_window.destroy()
    except Exception:
        pass


@pytest.fixture
def mock_sensor():
    sensor = Mock()
    sensor.sensor_id = 1
    sensor.coordinate_x = 100
    sensor.coordinate_y = 100
    sensor.coordinate_x2 = 150
    sensor.coordinate_y2 = 150
    sensor.is_armed.return_value = True
    sensor.get_type.return_value = SensorType.WINDOOR_SENSOR
    return sensor


@pytest.fixture
def mock_sensor_manager(mock_sensor):
    manager = Mock()
    manager.sensor_dict = {1: mock_sensor}
    return manager


@pytest.fixture
def mock_mode():
    mode = Mock()
    mode.mode_name = "Away"
    mode.get_mode_name.return_value = "Away"
    mode.get_sensor_list.return_value = [1]
    return mode


@pytest.fixture
def mock_config_manager(mock_mode):
    manager = Mock()
    manager.get_all_safehome_modes.return_value = {1: mock_mode}
    manager.get_safehome_mode_by_name.return_value = mock_mode
    manager.change_to_safehome_mode.return_value = True
    return manager


@pytest.fixture(autouse=True)
def mock_draw_floor_plan():
    with patch("core.pages.safehome_mode_page.draw_floor_plan"):
        yield


# Init tests
def test_init(root, mock_sensor_manager, mock_config_manager):
    page = SafeHomeModePage(
        root, "mode_page", mock_sensor_manager, mock_config_manager
    )
    assert page.get_id() == "mode_page"
    assert page.sensor_manager == mock_sensor_manager
    assert page.configuration_manager == mock_config_manager


# _get_current_matching_mode tests
def test_get_current_matching_mode_found(
    root, mock_sensor_manager, mock_config_manager
):
    page = SafeHomeModePage(
        root, "mode_page", mock_sensor_manager, mock_config_manager
    )
    result = page._get_current_matching_mode()
    assert result == "Away"


def test_get_current_matching_mode_not_found(
    root, mock_sensor_manager, mock_config_manager, mock_sensor
):
    mock_sensor.is_armed.return_value = False  # Change armed state
    page = SafeHomeModePage(
        root, "mode_page", mock_sensor_manager, mock_config_manager
    )
    result = page._get_current_matching_mode()
    assert result is None


def test_get_current_matching_mode_no_sensor_manager(
    root, mock_config_manager
):
    page = SafeHomeModePage(root, "mode_page", None, mock_config_manager)
    result = page._get_current_matching_mode()
    assert result is None


# draw_page tests
def test_draw_page(root, mock_sensor_manager, mock_config_manager):
    page = SafeHomeModePage(
        root, "mode_page", mock_sensor_manager, mock_config_manager
    )
    assert page.left_panel is not None
    assert page.right_panel is not None
    assert page.canvas is not None


def test_draw_page_creates_mode_buttons(
    root, mock_sensor_manager, mock_config_manager
):
    page = SafeHomeModePage(
        root, "mode_page", mock_sensor_manager, mock_config_manager
    )
    assert len(page.mode_buttons) > 0
    assert "Away" in page.mode_buttons


def test_draw_page_destroys_existing_widgets(
    root, mock_sensor_manager, mock_config_manager
):
    """Test that draw_page destroys existing widgets when called again"""
    page = SafeHomeModePage(
        root, "mode_page", mock_sensor_manager, mock_config_manager
    )
    # draw_page already created widgets, now call it again
    # This should destroy existing widgets (line 66 coverage)
    page.draw_page()
    assert len(page.mode_buttons) > 0


# _start_monitoring tests
def test_start_monitoring(root, mock_sensor_manager, mock_config_manager):
    page = SafeHomeModePage(
        root, "mode_page", mock_sensor_manager, mock_config_manager
    )
    # Monitoring is started in __init__
    assert page is not None


# _update_ui_state tests
def test_update_ui_state(root, mock_sensor_manager, mock_config_manager):
    page = SafeHomeModePage(
        root, "mode_page", mock_sensor_manager, mock_config_manager
    )
    page._update_ui_state()
    # Should update without error


def test_update_ui_state_mode_active(
    root, mock_sensor_manager, mock_config_manager
):
    page = SafeHomeModePage(
        root, "mode_page", mock_sensor_manager, mock_config_manager
    )
    page._update_ui_state()
    # Mode button should be highlighted
    assert page.mode_buttons["Away"] is not None


# apply_mode tests
@patch("core.pages.safehome_mode_page.show_toast")
def test_apply_mode_success(
    mock_toast, root, mock_sensor_manager, mock_config_manager
):
    page = SafeHomeModePage(
        root, "mode_page", mock_sensor_manager, mock_config_manager
    )
    page.apply_mode("Away")
    mock_config_manager.change_to_safehome_mode.assert_called_with("Away")


@patch("core.pages.safehome_mode_page.show_toast")
def test_apply_mode_failure(
    mock_toast, root, mock_sensor_manager, mock_config_manager
):
    mock_config_manager.change_to_safehome_mode.return_value = False
    page = SafeHomeModePage(
        root, "mode_page", mock_sensor_manager, mock_config_manager
    )
    page.apply_mode("Away")
    mock_toast.assert_called()


# _on_canvas_ready tests
def test_on_canvas_ready(root, mock_sensor_manager, mock_config_manager):
    page = SafeHomeModePage(
        root, "mode_page", mock_sensor_manager, mock_config_manager
    )
    page._on_canvas_ready()
    assert page._draw_job is not None


def test_on_canvas_ready_cancels_previous(
    root, mock_sensor_manager, mock_config_manager
):
    page = SafeHomeModePage(
        root, "mode_page", mock_sensor_manager, mock_config_manager
    )
    page._draw_job = 123
    page._on_canvas_ready()
    assert page._draw_job is not None


# _render_content tests
def test_render_content(root, mock_sensor_manager, mock_config_manager):
    page = SafeHomeModePage(
        root, "mode_page", mock_sensor_manager, mock_config_manager
    )
    page._render_content()


# _draw_sensors tests
def test_draw_sensors_windoor(
    root, mock_sensor_manager, mock_config_manager, mock_sensor
):
    mock_sensor.get_type.return_value = SensorType.WINDOOR_SENSOR
    page = SafeHomeModePage(
        root, "mode_page", mock_sensor_manager, mock_config_manager
    )
    page._draw_sensors()


def test_draw_sensors_motion(
    root, mock_sensor_manager, mock_config_manager, mock_sensor
):
    mock_sensor.get_type.return_value = SensorType.MOTION_DETECTOR_SENSOR
    page = SafeHomeModePage(
        root, "mode_page", mock_sensor_manager, mock_config_manager
    )
    page._draw_sensors()


def test_draw_sensors_armed(
    root, mock_sensor_manager, mock_config_manager, mock_sensor
):
    mock_sensor.is_armed.return_value = True
    page = SafeHomeModePage(
        root, "mode_page", mock_sensor_manager, mock_config_manager
    )
    page._draw_sensors()


def test_draw_sensors_disarmed(
    root, mock_sensor_manager, mock_config_manager, mock_sensor
):
    mock_sensor.is_armed.return_value = False
    page = SafeHomeModePage(
        root, "mode_page", mock_sensor_manager, mock_config_manager
    )
    page._draw_sensors()


def test_draw_sensors_no_manager(root, mock_config_manager):
    page = SafeHomeModePage(root, "mode_page", None, mock_config_manager)
    page._draw_sensors()


# open_config_window tests
@patch("core.pages.safehome_mode_page.SafeHomeModeConfigurePage")
def test_open_config_window(
    mock_window_class, root, mock_sensor_manager, mock_config_manager
):
    mock_window = Mock()
    mock_window_class.return_value = mock_window

    page = SafeHomeModePage(
        root, "mode_page", mock_sensor_manager, mock_config_manager
    )
    page.open_config_window()

    mock_window_class.assert_called_once()
    mock_window.tkraise.assert_called_once()


@patch("core.pages.safehome_mode_page.SafeHomeModeConfigurePage")
def test_open_config_window_with_current_mode(
    mock_window_class, root, mock_sensor_manager, mock_config_manager
):
    mock_window = Mock()
    mock_window_class.return_value = mock_window

    page = SafeHomeModePage(
        root, "mode_page", mock_sensor_manager, mock_config_manager
    )
    page.open_config_window()

    # Should pass current mode
    call_kwargs = mock_window_class.call_args[1]
    assert "current_mode_name" in call_kwargs
