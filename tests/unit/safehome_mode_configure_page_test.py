"""
Unit tests for safehome_mode_configure_page.py
Tests SafeHomeModeConfigurePage class with 100% coverage
"""

from unittest.mock import Mock, patch

import customtkinter as ctk
import pytest

from core.pages.safehome_mode_configure_page import SafeHomeModeConfigurePage
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
    sensor.get_type.return_value = SensorType.WINDOOR_SENSOR
    sensor.get_id.return_value = 1
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
    manager.update_safehome_mode.return_value = True
    return manager


@pytest.fixture(autouse=True)
def mock_toast():
    with patch("core.pages.safehome_mode_configure_page.show_toast"):
        yield


# Init tests
def test_init(root, mock_sensor_manager, mock_config_manager):
    page = SafeHomeModeConfigurePage(
        root, "config", mock_sensor_manager, mock_config_manager
    )
    assert page.get_id() == "config"


def test_init_custom_mode(root, mock_sensor_manager, mock_config_manager):
    page = SafeHomeModeConfigurePage(
        root,
        "config",
        mock_sensor_manager,
        mock_config_manager,
        current_mode_name="Home",
    )
    assert page.selected_mode_name.get() == "Away"  # Defaults to first mode


# draw_page tests
def test_draw_page(root, mock_sensor_manager, mock_config_manager):
    page = SafeHomeModeConfigurePage(
        root, "config", mock_sensor_manager, mock_config_manager
    )
    assert page.mode_selector is not None


def test_draw_page_no_modes(root, mock_sensor_manager):
    manager = Mock()
    manager.get_all_safehome_modes.return_value = {}

    page = SafeHomeModeConfigurePage(
        root, "config", mock_sensor_manager, manager
    )
    assert page.selected_mode_name is not None


# _draw_sensor_checkboxes tests
def test_draw_sensor_checkboxes(
    root, mock_sensor_manager, mock_config_manager
):
    page = SafeHomeModeConfigurePage(
        root, "config", mock_sensor_manager, mock_config_manager
    )
    assert 1 in page.sensor_check_dict


def test_draw_sensor_checkboxes_windoor(
    root, mock_sensor_manager, mock_config_manager, mock_sensor
):
    mock_sensor.get_type.return_value = SensorType.WINDOOR_SENSOR
    page = SafeHomeModeConfigurePage(
        root, "config", mock_sensor_manager, mock_config_manager
    )
    assert page.sensor_check_dict[1].get() is True


def test_draw_sensor_checkboxes_motion(
    root, mock_sensor_manager, mock_config_manager, mock_sensor
):
    mock_sensor.get_type.return_value = SensorType.MOTION_DETECTOR_SENSOR
    page = SafeHomeModeConfigurePage(
        root, "config", mock_sensor_manager, mock_config_manager
    )
    assert 1 in page.sensor_check_dict


def test_draw_sensor_checkboxes_unselected(
    root, mock_sensor_manager, mock_config_manager, mock_mode
):
    mock_mode.get_sensor_list.return_value = []
    page = SafeHomeModeConfigurePage(
        root, "config", mock_sensor_manager, mock_config_manager
    )
    assert page.sensor_check_dict[1].get() is False


# _on_mode_change tests
def test_on_mode_change(root, mock_sensor_manager, mock_config_manager):
    page = SafeHomeModeConfigurePage(
        root, "config", mock_sensor_manager, mock_config_manager
    )
    page._on_mode_change("Away")


# _save_configuration tests
def test_save_configuration_success(
    root, mock_sensor_manager, mock_config_manager
):
    page = SafeHomeModeConfigurePage(
        root, "config", mock_sensor_manager, mock_config_manager
    )

    with patch.object(page, "destroy"):
        page._save_configuration()

    mock_config_manager.update_safehome_mode.assert_called_once()


def test_save_configuration_selected(
    root, mock_sensor_manager, mock_config_manager
):
    page = SafeHomeModeConfigurePage(
        root, "config", mock_sensor_manager, mock_config_manager
    )
    page.sensor_check_dict[1].set(True)

    with patch.object(page, "destroy"):
        page._save_configuration()


def test_save_configuration_unselected(
    root, mock_sensor_manager, mock_config_manager
):
    page = SafeHomeModeConfigurePage(
        root, "config", mock_sensor_manager, mock_config_manager
    )
    page.sensor_check_dict[1].set(False)

    with patch.object(page, "destroy"):
        page._save_configuration()


def test_save_configuration_failure(
    root, mock_sensor_manager, mock_config_manager
):
    mock_config_manager.update_safehome_mode.return_value = False

    page = SafeHomeModeConfigurePage(
        root, "config", mock_sensor_manager, mock_config_manager
    )

    with patch.object(page, "destroy") as mock_destroy:
        page._save_configuration()
        mock_destroy.assert_not_called()


# Additional coverage tests
def test_save_configuration_no_manager(
    root, mock_sensor_manager, mock_config_manager
):
    page = SafeHomeModeConfigurePage(
        root, "config", mock_sensor_manager, mock_config_manager
    )
    # Set manager to None after initialization
    page.configuration_manager = None

    with patch.object(page, "destroy") as mock_destroy:
        page._save_configuration()
        mock_destroy.assert_not_called()


def test_save_configuration_mode_not_found(
    root, mock_sensor_manager, mock_config_manager
):
    mock_config_manager.get_safehome_mode_by_name.return_value = None

    page = SafeHomeModeConfigurePage(
        root, "config", mock_sensor_manager, mock_config_manager
    )

    with patch.object(page, "destroy") as mock_destroy:
        page._save_configuration()
        mock_destroy.assert_not_called()


def test_save_configuration_exception(
    root, mock_sensor_manager, mock_config_manager
):
    mock_config_manager.get_safehome_mode_by_name.side_effect = Exception(
        "Test error"
    )

    page = SafeHomeModeConfigurePage(
        root, "config", mock_sensor_manager, mock_config_manager
    )

    with patch.object(page, "destroy") as mock_destroy:
        page._save_configuration()
        mock_destroy.assert_not_called()
