"""
Unit tests for sensors_management_page.py
Tests SensorsManagementPage class with 100% coverage
"""

from unittest.mock import Mock, patch

import customtkinter as ctk
import pytest

from core.pages.sensors_management_page import SensorsManagementPage
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
def mock_wd_sensor():
    sensor = Mock()
    sensor.sensor_id = 1
    sensor.get_type.return_value = SensorType.WINDOOR_SENSOR
    sensor.get_id.return_value = 1
    sensor.is_enabled.return_value = True
    sensor.get_physical_status.return_value = "normal"
    return sensor


@pytest.fixture
def mock_md_sensor():
    sensor = Mock()
    sensor.sensor_id = 2
    sensor.get_type.return_value = SensorType.MOTION_DETECTOR_SENSOR
    sensor.get_id.return_value = 2
    sensor.is_enabled.return_value = True
    sensor.get_physical_status.return_value = "normal"
    return sensor


@pytest.fixture
def mock_sensor_manager(mock_wd_sensor, mock_md_sensor):
    manager = Mock()
    manager.sensor_dict = {1: mock_wd_sensor, 2: mock_md_sensor}
    return manager


# Init tests
def test_init_with_sensors(root, mock_sensor_manager):
    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)
    assert page.get_id() == "sensors"
    assert "1-1" in page.rangeSensorID_WinDoorSensor.get()


def test_init_no_wd_sensors(root, mock_md_sensor):
    manager = Mock()
    manager.sensor_dict = {2: mock_md_sensor}

    page = SensorsManagementPage(root, "sensors", manager)
    assert page.rangeSensorID_WinDoorSensor.get() == "None"


def test_init_no_md_sensors(root, mock_wd_sensor):
    manager = Mock()
    manager.sensor_dict = {1: mock_wd_sensor}

    page = SensorsManagementPage(root, "sensors", manager)
    assert page.rangeSensorID_MotionDetector.get() == "None"


def test_init_no_sensors(root):
    manager = Mock()
    manager.sensor_dict = {}

    page = SensorsManagementPage(root, "sensors", manager)
    assert page.rangeSensorID_WinDoorSensor.get() == "None"
    assert page.rangeSensorID_MotionDetector.get() == "None"


# draw_page test
def test_draw_page(root, mock_sensor_manager):
    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)
    assert page is not None


# _validate_digits tests
def test_validate_digits_valid(root, mock_sensor_manager):
    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)
    assert page._validate_digits("123") is True


def test_validate_digits_empty(root, mock_sensor_manager):
    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)
    assert page._validate_digits("") is False


def test_validate_digits_invalid(root, mock_sensor_manager):
    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)
    assert page._validate_digits("abc") is False


# _get_target_sensor tests
def test_get_target_sensor_windoor_valid(root, mock_sensor_manager):
    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)
    page.inputSensorID_WinDoorSensor.set("1")

    sensor_id, sensor = page._get_target_sensor("windoor")
    assert sensor_id == 1
    assert sensor is not None


def test_get_target_sensor_windoor_empty(root, mock_sensor_manager):
    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)
    page.inputSensorID_WinDoorSensor.set("")

    with patch("tkinter.messagebox.showinfo"):
        sensor_id, sensor = page._get_target_sensor("windoor")
        assert sensor_id is None


def test_get_target_sensor_windoor_invalid_digits(root, mock_sensor_manager):
    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)
    page.inputSensorID_WinDoorSensor.set("abc")

    with patch("tkinter.messagebox.showinfo"):
        sensor_id, sensor = page._get_target_sensor("windoor")
        assert sensor_id is None


def test_get_target_sensor_windoor_not_found(root, mock_sensor_manager):
    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)
    page.inputSensorID_WinDoorSensor.set("999")

    with patch("tkinter.messagebox.showinfo"):
        sensor_id, sensor = page._get_target_sensor("windoor")
        assert sensor_id is None


def test_get_target_sensor_windoor_wrong_type(
    root, mock_sensor_manager, mock_md_sensor
):
    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)
    page.inputSensorID_WinDoorSensor.set("2")  # MD sensor ID

    with patch("tkinter.messagebox.showinfo"):
        sensor_id, sensor = page._get_target_sensor("windoor")
        assert sensor_id is None


def test_get_target_sensor_motion_valid(root, mock_sensor_manager):
    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)
    page.inputSensorID_MotionDetector.set("2")

    sensor_id, sensor = page._get_target_sensor("motion")
    assert sensor_id == 2


# _handle_sensor_action tests
def test_handle_sensor_action_arm(root, mock_sensor_manager):
    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)
    page.inputSensorID_WinDoorSensor.set("1")

    with patch.object(page, "_update_status"):
        page._handle_sensor_action("windoor", "arm")

    mock_sensor_manager.arm_sensor.assert_called_once_with(1)


def test_handle_sensor_action_disarm(root, mock_sensor_manager):
    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)
    page.inputSensorID_WinDoorSensor.set("1")

    with patch.object(page, "_update_status"):
        page._handle_sensor_action("windoor", "disarm")

    mock_sensor_manager.disarm_sensor.assert_called_once_with(1)


def test_handle_sensor_action_invalid_sensor(root, mock_sensor_manager):
    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)
    page.inputSensorID_WinDoorSensor.set("999")

    with patch("tkinter.messagebox.showinfo"):
        page._handle_sensor_action("windoor", "arm")


# _execute_physical_action tests
def test_execute_physical_action_intrude(root, mock_sensor_manager):
    import time

    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)
    page.inputSensorID_WinDoorSensor.set("1")

    with patch.object(page, "_update_status"):
        page._execute_physical_action("windoor", "intrude")

    mock_sensor_manager.intrude_sensor.assert_called_once_with(1)
    time.sleep(1.1)  # Wait for rate limit to reset


def test_execute_physical_action_release(root, mock_sensor_manager):
    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)
    page.inputSensorID_MotionDetector.set("2")

    with patch.object(page, "_update_status"):
        page._execute_physical_action("motion", "release")

    mock_sensor_manager.release_sensor.assert_called_once_with(2)


# _handle_physical_action tests
def test_handle_physical_action_success(root, mock_sensor_manager):
    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)
    page.inputSensorID_WinDoorSensor.set("1")

    with patch.object(page, "_execute_physical_action"):
        page._handle_physical_action("windoor", "intrude")


def test_handle_physical_action_rate_limit(root, mock_sensor_manager):
    from ratelimit import RateLimitException

    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)
    page.inputSensorID_WinDoorSensor.set("1")

    with patch.object(
        page,
        "_execute_physical_action",
        side_effect=RateLimitException("Rate limit", 60),
    ):
        with patch("tkinter.messagebox.showwarning"):
            page._handle_physical_action("windoor", "intrude")


# _update_status tests
def test_update_status(root, mock_sensor_manager):
    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)
    page._update_status()


def test_update_status_disabled(root, mock_sensor_manager, mock_wd_sensor):
    mock_wd_sensor.is_enabled.return_value = False
    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)
    page._update_status()


def test_update_status_triggered(root, mock_sensor_manager, mock_wd_sensor):
    mock_wd_sensor.get_physical_status.return_value = "triggered"
    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)
    page._update_status()


def test_update_status_problem(root, mock_sensor_manager, mock_wd_sensor):
    mock_wd_sensor.get_physical_status.return_value = "problem"
    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)
    page._update_status()


def test_update_status_no_test_armed_state(
    root, mock_sensor_manager, mock_wd_sensor
):
    # Remove test_armed_state method to trigger getattr fallback (line 335)
    del mock_wd_sensor.test_armed_state
    mock_wd_sensor.armed = True
    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)
    page._update_status()


def test_update_status_exception(root, mock_sensor_manager, mock_wd_sensor):
    """Test exception handling in _update_status method."""
    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)

    # Set side_effect AFTER page initialization to trigger exception in
    # _update_status
    mock_wd_sensor.get_type.side_effect = Exception("Test error")

    # This should catch the exception and print an error message
    with patch("builtins.print") as mock_print:
        # Call _update_status directly (bypass the after scheduling)
        with patch.object(page, "after"):
            page._update_status()
        mock_print.assert_called()


# _handle_all_sensors tests
def test_handle_all_sensors_arm(root, mock_sensor_manager):
    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)

    with patch.object(page, "_update_status"):
        page._handle_all_sensors("arm")

    mock_sensor_manager.arm_all_sensors.assert_called_once()


def test_handle_all_sensors_disarm(root, mock_sensor_manager):
    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)

    with patch.object(page, "_update_status"):
        page._handle_all_sensors("disarm")

    mock_sensor_manager.disarm_all_sensors.assert_called_once()


def test_handle_all_sensors_invalid_action(root, mock_sensor_manager):
    page = SensorsManagementPage(root, "sensors", mock_sensor_manager)

    with patch.object(page, "_update_status"):
        page._handle_all_sensors("invalid")
