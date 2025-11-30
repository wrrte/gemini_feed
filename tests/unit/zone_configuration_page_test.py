"""
Unit tests for zone_configuration_page.py
Tests ZoneConfigurationWindow class with 100% coverage
"""

from unittest.mock import Mock, patch

import customtkinter as ctk
import pytest

from core.pages.zone_configuration_page import ZoneConfigurationWindow
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
    sensor.get_type.return_value = SensorType.WINDOOR_SENSOR
    return sensor


@pytest.fixture
def mock_sensor_manager(mock_sensor):
    manager = Mock()
    manager.sensor_dict = {1: mock_sensor}
    return manager


@pytest.fixture
def mock_zone():
    zone = Mock()
    zone.get_zone_id.return_value = 1
    zone.get_zone_name.return_value = "TestZone"
    zone.get_coordinates.return_value = (50, 50, 200, 200)
    zone.get_sensor_list.return_value = [1]
    return zone


@pytest.fixture
def mock_config_manager(mock_zone):
    manager = Mock()
    manager.get_safety_zone.return_value = mock_zone
    manager.get_all_safety_zones.return_value = {1: mock_zone}
    manager.add_safety_zone.return_value = True
    manager.update_safety_zone.return_value = None
    manager._check_zone_is_overlap.return_value = False
    return manager


@pytest.fixture
def mock_callback():
    return Mock()


@pytest.fixture(autouse=True)
def mock_draw_floor_plan():
    with patch("core.pages.zone_configuration_page.draw_floor_plan"):
        yield


# Init tests
def test_init_add_mode(
    root, mock_sensor_manager, mock_config_manager, mock_callback
):
    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
    )
    assert window.get_id() == "zone_cfg"
    assert window.target_zone_id is None


def test_init_edit_mode(
    root, mock_sensor_manager, mock_config_manager, mock_callback
):
    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
        zone_id=1,
    )
    assert window.target_zone_id == 1
    assert 1 in window.selected_sensors


def test_init_edit_mode_no_zone(
    root, mock_sensor_manager, mock_config_manager, mock_callback
):
    mock_config_manager.get_safety_zone.return_value = None
    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
        zone_id=1,
    )
    assert window.display_name == ""


# _load_initial_data tests
def test_load_initial_data_with_coords(
    root, mock_sensor_manager, mock_config_manager, mock_callback, mock_zone
):
    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
        zone_id=1,
    )
    assert window.current_coords["x1"] == 50


def test_load_initial_data_no_coords(
    root, mock_sensor_manager, mock_config_manager, mock_callback
):
    zone = Mock()
    zone.get_coordinates.return_value = None
    zone.get_sensor_list.return_value = []
    mock_config_manager.get_safety_zone.return_value = zone

    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
        zone_id=1,
    )
    assert window.current_coords["x1"] is None


# draw_page tests
def test_draw_page_creates_widgets(
    root, mock_sensor_manager, mock_config_manager, mock_callback
):
    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
    )
    assert window.canvas is not None
    assert window.name_entry is not None


# _redraw_canvas tests
def test_redraw_canvas(
    root, mock_sensor_manager, mock_config_manager, mock_callback
):
    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
    )
    window._redraw_canvas()


def test_redraw_canvas_with_selection(
    root, mock_sensor_manager, mock_config_manager, mock_callback
):
    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
    )
    window.selected_sensors.add(1)
    window._redraw_canvas()


def test_redraw_canvas_motion_sensor(
    root, mock_sensor_manager, mock_config_manager, mock_callback, mock_sensor
):
    mock_sensor.get_type.return_value = SensorType.MOTION_DETECTOR_SENSOR
    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
    )
    window._redraw_canvas()


def test_redraw_canvas_with_coords(
    root, mock_sensor_manager, mock_config_manager, mock_callback
):
    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
    )
    window.current_coords = {"x1": 10, "y1": 10, "x2": 100, "y2": 100}
    window._redraw_canvas()


# Mouse event tests
def test_on_mouse_press(
    root, mock_sensor_manager, mock_config_manager, mock_callback
):
    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
    )
    event = Mock()
    event.x = 100
    event.y = 150
    window._on_mouse_press(event)
    assert window.drag_start["x"] == 100


def test_on_mouse_press_clamp(
    root, mock_sensor_manager, mock_config_manager, mock_callback
):
    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
    )
    event = Mock()
    event.x = 600
    event.y = 400
    window._on_mouse_press(event)
    assert window.drag_start["x"] == 500
    assert window.drag_start["y"] == 312


def test_on_mouse_drag(
    root, mock_sensor_manager, mock_config_manager, mock_callback
):
    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
    )
    window.drag_start = {"x": 100, "y": 100}

    event = Mock()
    event.x = 200
    event.y = 200

    with patch.object(window, "_redraw_canvas"):
        window._on_mouse_drag(event)

    assert window.current_coords["x1"] == 100
    assert window.current_coords["x2"] == 200


def test_on_mouse_drag_no_start(
    root, mock_sensor_manager, mock_config_manager, mock_callback
):
    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
    )
    event = Mock()
    event.x = 200
    event.y = 200

    with patch.object(window, "_redraw_canvas") as mock_redraw:
        window._on_mouse_drag(event)
        mock_redraw.assert_not_called()


def test_on_mouse_drag_with_sensor_selection(
    root, mock_sensor_manager, mock_config_manager, mock_callback
):
    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
    )
    window.drag_start = {"x": 50, "y": 50}

    event = Mock()
    event.x = 200
    event.y = 200

    with patch(
        "core.pages.zone_configuration_page.is_sensor_in_rect",
        return_value=True,
    ):
        with patch.object(window, "_redraw_canvas"):
            window._on_mouse_drag(event)

        assert 1 in window.selected_sensors


def test_on_mouse_release(
    root, mock_sensor_manager, mock_config_manager, mock_callback
):
    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
    )
    window.drag_start = {"x": 100, "y": 100}

    event = Mock()
    window._on_mouse_release(event)

    assert window.drag_start["x"] is None


def test_on_sensor_click_toggle_on(
    root, mock_sensor_manager, mock_config_manager, mock_callback
):
    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
    )

    event = Mock()
    event.x = 100
    event.y = 100

    window.canvas.find_overlapping = Mock(return_value=[1])
    window.canvas.gettags = Mock(return_value=["sensor_1"])

    with patch.object(window, "_redraw_canvas"):
        window._on_sensor_click(event)

    assert 1 in window.selected_sensors


def test_on_sensor_click_toggle_off(
    root, mock_sensor_manager, mock_config_manager, mock_callback
):
    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
    )
    window.selected_sensors.add(1)

    event = Mock()
    event.x = 100
    event.y = 100

    window.canvas.find_overlapping = Mock(return_value=[1])
    window.canvas.gettags = Mock(return_value=["sensor_1"])

    with patch.object(window, "_redraw_canvas"):
        window._on_sensor_click(event)

    assert 1 not in window.selected_sensors


def test_on_sensor_click_no_sensor(
    root, mock_sensor_manager, mock_config_manager, mock_callback
):
    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
    )

    event = Mock()
    event.x = 10
    event.y = 10

    window.canvas.find_overlapping = Mock(return_value=[])

    with patch.object(window, "_redraw_canvas") as mock_redraw:
        window._on_sensor_click(event)
        mock_redraw.assert_not_called()


# _confirm_zone tests
def test_confirm_zone_add_success(
    root, mock_sensor_manager, mock_config_manager, mock_callback
):
    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
    )
    window.name_entry.insert(0, "NewZone")
    window.current_coords = {"x1": 50, "y1": 50, "x2": 200, "y2": 200}
    window.selected_sensors.add(1)

    with patch(
        "core.pages.zone_configuration_page.find_lowest_empty_id",
        return_value=10,
    ):
        with patch.object(window, "destroy"):
            window._confirm_zone()

    mock_config_manager.add_safety_zone.assert_called_once()
    mock_callback.assert_called_once()


def test_confirm_zone_update_success(
    root, mock_sensor_manager, mock_config_manager, mock_callback
):
    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
        zone_id=1,
    )
    window.name_entry.delete(0, "end")
    window.name_entry.insert(0, "UpdatedZone")
    window.current_coords = {"x1": 50, "y1": 50, "x2": 200, "y2": 200}

    with patch.object(window, "destroy"):
        window._confirm_zone()

    mock_config_manager.update_safety_zone.assert_called_once()


def test_confirm_zone_no_name(
    root, mock_sensor_manager, mock_config_manager, mock_callback
):
    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
    )
    window.current_coords = {"x1": 50, "y1": 50, "x2": 200, "y2": 200}

    window._confirm_zone()

    assert window.name_error_label.cget("text") == "Name required"


def test_confirm_zone_no_coords(
    root, mock_sensor_manager, mock_config_manager, mock_callback
):
    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
    )
    window.name_entry.insert(0, "Zone")

    window._confirm_zone()

    assert "Draw zone area first" in window.error_label.cget("text")


def test_confirm_zone_overlap(
    root, mock_sensor_manager, mock_config_manager, mock_callback
):
    mock_config_manager._check_zone_is_overlap.return_value = True

    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
    )
    window.name_entry.insert(0, "Zone")
    window.current_coords = {"x1": 50, "y1": 50, "x2": 200, "y2": 200}

    window._confirm_zone()

    assert "overlapping" in window.error_label.cget("text")


def test_confirm_zone_duplicate_name(
    root, mock_sensor_manager, mock_config_manager, mock_callback, mock_zone
):
    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
    )
    window.name_entry.insert(0, "testzone")  # Same name in different case
    window.current_coords = {"x1": 50, "y1": 50, "x2": 200, "y2": 200}

    window._confirm_zone()

    assert "Name exists" in window.name_error_label.cget("text")


def test_confirm_zone_add_failure(
    root, mock_sensor_manager, mock_config_manager, mock_callback
):
    mock_config_manager.add_safety_zone.return_value = False

    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
    )
    window.name_entry.insert(0, "NewZone")
    window.current_coords = {"x1": 50, "y1": 50, "x2": 200, "y2": 200}
    mock_config_manager.get_all_safety_zones.return_value = {}

    with patch(
        "core.pages.zone_configuration_page.find_lowest_empty_id",
        return_value=10,
    ):
        window._confirm_zone()

    assert "Failed to create zone" in window.error_label.cget("text")


def test_confirm_zone_add_with_sensors(
    root, mock_sensor_manager, mock_config_manager, mock_callback
):
    new_zone = Mock()
    mock_config_manager.get_safety_zone.return_value = new_zone
    mock_config_manager.get_all_safety_zones.return_value = {}

    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
    )
    window.name_entry.insert(0, "NewZone")
    window.current_coords = {"x1": 50, "y1": 50, "x2": 200, "y2": 200}
    window.selected_sensors.add(1)

    with patch(
        "core.pages.zone_configuration_page.find_lowest_empty_id",
        return_value=10,
    ):
        with patch.object(window, "destroy"):
            window._confirm_zone()

    new_zone.set_sensor_list.assert_called_once()


def test_confirm_zone_update_with_sensors(
    root, mock_sensor_manager, mock_config_manager, mock_callback, mock_zone
):
    # mock_zone already configured properly with get_coordinates
    window = ZoneConfigurationWindow(
        root,
        "zone_cfg",
        mock_sensor_manager,
        mock_config_manager,
        mock_callback,
        zone_id=1,
    )
    window.name_entry.delete(0, "end")
    window.name_entry.insert(0, "UpdatedZone")
    window.current_coords = {"x1": 50, "y1": 50, "x2": 200, "y2": 200}
    window.selected_sensors.add(1)

    with patch.object(window, "destroy"):
        window._confirm_zone()

    mock_zone.set_sensor_list.assert_called_once_with([1])
