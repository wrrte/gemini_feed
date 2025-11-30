"""
Unit tests for security_page.py
Tests SecurityPage class - core logic only (UI excluded)
"""

from unittest.mock import Mock, patch

import customtkinter as ctk
import pytest

from core.pages.security_page import SecurityPage
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
    sensor.is_armed.return_value = True
    return sensor


@pytest.fixture
def mock_motion_sensor():
    sensor = Mock()
    sensor.sensor_id = 2
    sensor.coordinate_x = 50
    sensor.coordinate_y = 50
    sensor.coordinate_x2 = 100
    sensor.coordinate_y2 = 100
    sensor.get_type.return_value = SensorType.MOTION_DETECTOR_SENSOR
    sensor.is_armed.return_value = False
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
    zone.is_armed.return_value = False
    return zone


@pytest.fixture
def mock_config_manager(mock_zone):
    manager = Mock()
    manager.get_all_safety_zones.return_value = {1: mock_zone}
    manager.get_safety_zone.return_value = mock_zone
    manager.arm_safety_zone.return_value = True
    manager.disarm_safety_zone.return_value = True
    manager.delete_safety_zone.return_value = True
    return manager


@pytest.fixture
def mock_login_manager():
    manager = Mock()
    manager.current_user_id = "testuser"
    manager._verify_web_password.return_value = True
    return manager


@pytest.fixture(autouse=True)
def mock_show_toast():
    with patch("core.pages.security_page.show_toast"):
        yield


# Init tests
def test_init(root, mock_sensor_manager, mock_config_manager):
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        configuration_manager=mock_config_manager,
    )
    assert page.get_id() == "security"
    assert page.sensor_manager == mock_sensor_manager


def test_init_with_login_manager(
    root, mock_sensor_manager, mock_config_manager, mock_login_manager
):
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    assert page.login_manager == mock_login_manager


def test_init_no_managers(root, mock_sensor_manager):
    page = SecurityPage(root, mock_sensor_manager, "security")
    assert page.configuration_manager is None


# _sync_sensors_to_zones tests
def test_sync_sensors_to_zones(
    root, mock_sensor_manager, mock_config_manager, mock_zone
):
    with patch(
        "core.pages.security_page.is_sensor_in_rect", return_value=True
    ):
        SecurityPage(
            root,
            mock_sensor_manager,
            "security",
            configuration_manager=mock_config_manager,
        )
    mock_zone.set_sensor_list.assert_called()


def test_sync_sensors_to_zones_no_config(root, mock_sensor_manager):
    SecurityPage(root, mock_sensor_manager, "security")


def test_sync_sensors_to_zones_no_sensors(root, mock_config_manager):
    manager = Mock()
    manager.sensor_dict = {}
    SecurityPage(
        root, manager, "security", configuration_manager=mock_config_manager
    )


def test_sync_sensors_to_zones_no_coords(root, mock_sensor_manager, mock_zone):
    mock_zone.get_coordinates.return_value = None
    manager = Mock()
    manager.get_all_safety_zones.return_value = {1: mock_zone}

    SecurityPage(
        root, mock_sensor_manager, "security", configuration_manager=manager
    )


def test_sync_sensors_to_zones_sensor_not_in_zone(
    root, mock_sensor_manager, mock_config_manager
):
    with patch(
        "core.pages.security_page.is_sensor_in_rect", return_value=False
    ):
        SecurityPage(
            root,
            mock_sensor_manager,
            "security",
            configuration_manager=mock_config_manager,
        )


# tkraise tests
def test_tkraise(root, mock_sensor_manager):
    page = SecurityPage(root, mock_sensor_manager, "security")
    page.tkraise()


def test_tkraise_with_above(root, mock_sensor_manager):
    page = SecurityPage(root, mock_sensor_manager, "security")
    other_page = ctk.CTkFrame(root)
    page.tkraise(other_page)


# draw_page tests
def test_draw_page(root, mock_sensor_manager):
    page = SecurityPage(root, mock_sensor_manager, "security")
    page.draw_page()
    assert page._monitoring_active is False


def test_draw_page_destroys_widgets(root, mock_sensor_manager):
    page = SecurityPage(root, mock_sensor_manager, "security")
    label = ctk.CTkLabel(page, text="test")
    label.pack()
    page.draw_page()


# _get_ui_state_snapshot tests
def test_get_ui_state_snapshot(
    root, mock_sensor_manager, mock_config_manager, mock_zone
):
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        configuration_manager=mock_config_manager,
    )
    snapshot = page._get_ui_state_snapshot()
    assert snapshot is not None
    assert len(snapshot) == 3


def test_get_ui_state_snapshot_no_managers(root, mock_sensor_manager):
    page = SecurityPage(root, mock_sensor_manager, "security")
    page.configuration_manager = None
    page.sensor_manager = None
    snapshot = page._get_ui_state_snapshot()
    assert snapshot is not None


# _sync_zone_state_with_sensors tests
def test_sync_zone_state_with_sensors_armed(
    root, mock_sensor_manager, mock_config_manager, mock_zone, mock_sensor
):
    mock_sensor.is_armed.return_value = True
    mock_zone.get_sensor_list.return_value = [1]

    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        configuration_manager=mock_config_manager,
    )
    page._sync_zone_state_with_sensors()
    mock_zone.arm.assert_called()


def test_sync_zone_state_with_sensors_disarmed(
    root, mock_sensor_manager, mock_config_manager, mock_zone, mock_sensor
):
    mock_sensor.is_armed.return_value = False
    mock_zone.get_sensor_list.return_value = [1]

    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        configuration_manager=mock_config_manager,
    )
    page._sync_zone_state_with_sensors()
    mock_zone.disarm.assert_called()


def test_sync_zone_state_no_sensors(
    root, mock_sensor_manager, mock_config_manager, mock_zone
):
    mock_zone.get_sensor_list.return_value = []
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        configuration_manager=mock_config_manager,
    )
    page._sync_zone_state_with_sensors()


def test_sync_zone_state_sensor_not_found(
    root, mock_sensor_manager, mock_config_manager, mock_zone
):
    mock_zone.get_sensor_list.return_value = [999]  # Non-existent
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        configuration_manager=mock_config_manager,
    )
    page._sync_zone_state_with_sensors()


# Button handlers tests
def test_add_zone(root, mock_sensor_manager, mock_config_manager):
    with patch("core.pages.security_page.ZoneConfigurationWindow"):
        page = SecurityPage(
            root,
            mock_sensor_manager,
            "security",
            configuration_manager=mock_config_manager,
        )
        page.add_zone()


def test_update_zone_no_selection(
    root, mock_sensor_manager, mock_config_manager
):
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        configuration_manager=mock_config_manager,
    )
    page.selected_zone_id = None
    page.update_zone()


def test_update_zone_with_selection(
    root, mock_sensor_manager, mock_config_manager
):
    with patch("core.pages.security_page.ZoneConfigurationWindow"):
        page = SecurityPage(
            root,
            mock_sensor_manager,
            "security",
            configuration_manager=mock_config_manager,
        )
        page.selected_zone_id = 1
        page.update_zone()


def test_delete_zone_no_config(root, mock_sensor_manager):
    page = SecurityPage(root, mock_sensor_manager, "security")
    page.selected_zone_id = 1
    page.delete_zone()


def test_delete_zone_not_found(root, mock_sensor_manager, mock_config_manager):
    mock_config_manager.get_safety_zone.return_value = None
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        configuration_manager=mock_config_manager,
    )
    page.selected_zone_id = 1
    page.delete_zone()


def test_delete_zone_success(
    root, mock_sensor_manager, mock_config_manager, mock_zone
):
    with patch.object(SecurityPage, "_render_content"):
        with patch.object(SecurityPage, "_update_zone_status_list"):
            page = SecurityPage(
                root,
                mock_sensor_manager,
                "security",
                configuration_manager=mock_config_manager,
            )
            page.selected_zone_id = 1
            page.delete_zone()
    assert page.selected_zone_id is None


def test_delete_zone_failure(
    root, mock_sensor_manager, mock_config_manager, mock_zone
):
    mock_config_manager.delete_safety_zone.return_value = False
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        configuration_manager=mock_config_manager,
    )
    page.selected_zone_id = 1
    page.delete_zone()


def test_arm_zone_no_config(root, mock_sensor_manager):
    page = SecurityPage(root, mock_sensor_manager, "security")
    page.arm_zone()


def test_arm_zone_success(root, mock_sensor_manager, mock_config_manager):
    with patch.object(SecurityPage, "_render_content"):
        with patch.object(SecurityPage, "_update_zone_status_list"):
            page = SecurityPage(
                root,
                mock_sensor_manager,
                "security",
                configuration_manager=mock_config_manager,
            )
            page.selected_zone_id = 1
            page.arm_zone()


def test_arm_zone_failure(root, mock_sensor_manager, mock_config_manager):
    mock_config_manager.arm_safety_zone.return_value = False
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        configuration_manager=mock_config_manager,
    )
    page.selected_zone_id = 1
    page.arm_zone()


def test_disarm_zone_no_config(root, mock_sensor_manager):
    page = SecurityPage(root, mock_sensor_manager, "security")
    page.disarm_zone()


def test_disarm_zone_success(root, mock_sensor_manager, mock_config_manager):
    with patch.object(SecurityPage, "_render_content"):
        with patch.object(SecurityPage, "_update_zone_status_list"):
            page = SecurityPage(
                root,
                mock_sensor_manager,
                "security",
                configuration_manager=mock_config_manager,
            )
            page.selected_zone_id = 1
            page.disarm_zone()


def test_disarm_zone_failure(root, mock_sensor_manager, mock_config_manager):
    mock_config_manager.disarm_safety_zone.return_value = False
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        configuration_manager=mock_config_manager,
    )
    page.selected_zone_id = 1
    page.disarm_zone()


# Callback test
def test_on_zone_update_success(
    root, mock_sensor_manager, mock_config_manager
):
    with patch.object(SecurityPage, "_render_content"):
        with patch.object(SecurityPage, "_update_zone_status_list"):
            page = SecurityPage(
                root,
                mock_sensor_manager,
                "security",
                configuration_manager=mock_config_manager,
            )
            page._on_zone_update_success()


# =============================================================================
# Authentication and _draw_security_content tests
# =============================================================================


def find_widgets_by_type(parent, widget_type):
    """Recursively find all widgets of a specific type."""
    result = []
    for child in parent.winfo_children():
        if isinstance(child, widget_type):
            result.append(child)
        result.extend(find_widgets_by_type(child, widget_type))
    return result


def find_button_by_text(parent, text):
    """Find button by its text."""
    buttons = find_widgets_by_type(parent, ctk.CTkButton)
    for btn in buttons:
        if btn.cget("text") == text:
            return btn
    return None


def test_verify_password_empty(root, mock_sensor_manager, mock_login_manager):
    """Test verify_password with empty password"""
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
    )
    root.update_idletasks()

    # Find password entry and login button
    entries = find_widgets_by_type(page, ctk.CTkEntry)
    if entries:
        entries[0].delete(0, "end")
        root.update_idletasks()
        login_btn = find_button_by_text(page, "Login")
        if login_btn:
            login_btn.invoke()
            root.update_idletasks()

    # Should not call _draw_security_content
    assert not hasattr(page, "left_panel") or page.left_panel is None


def test_verify_password_no_login_manager(root, mock_sensor_manager):
    """Test verify_password without login manager"""
    page = SecurityPage(root, mock_sensor_manager, "security")
    root.update_idletasks()

    entries = find_widgets_by_type(page, ctk.CTkEntry)
    if entries:
        entries[0].delete(0, "end")
        entries[0].insert(0, "password123")
        root.update_idletasks()
        login_btn = find_button_by_text(page, "Login")
        if login_btn:
            login_btn.invoke()
            root.update_idletasks()

    # Should not call _draw_security_content
    assert not hasattr(page, "left_panel") or page.left_panel is None


def test_verify_password_no_user_id(
    root, mock_sensor_manager, mock_login_manager
):
    """Test verify_password without user ID"""
    mock_login_manager.current_user_id = None
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
    )
    root.update_idletasks()

    entries = find_widgets_by_type(page, ctk.CTkEntry)
    if entries:
        entries[0].delete(0, "end")
        entries[0].insert(0, "password123")
        root.update_idletasks()
        login_btn = find_button_by_text(page, "Login")
        if login_btn:
            login_btn.invoke()
            root.update_idletasks()

    # Should not call _draw_security_content
    assert not hasattr(page, "left_panel") or page.left_panel is None


def test_verify_password_incorrect(
    root, mock_sensor_manager, mock_login_manager
):
    """Test verify_password with incorrect password"""
    mock_login_manager._verify_web_password.return_value = False
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
    )
    root.update_idletasks()

    entries = find_widgets_by_type(page, ctk.CTkEntry)
    if entries:
        entries[0].delete(0, "end")
        entries[0].insert(0, "wrongpassword")
        root.update_idletasks()
        login_btn = find_button_by_text(page, "Login")
        if login_btn:
            login_btn.invoke()
            root.update_idletasks()

    # Should not call _draw_security_content
    assert not hasattr(page, "left_panel") or page.left_panel is None


def test_verify_password_success_calls_draw_security_content(
    root, mock_sensor_manager, mock_config_manager, mock_login_manager
):
    """Test verify_password success calls _draw_security_content"""
    mock_login_manager._verify_web_password.return_value = True
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    entries = find_widgets_by_type(page, ctk.CTkEntry)
    if entries:
        entries[0].delete(0, "end")
        entries[0].insert(0, "correctpassword")
        root.update_idletasks()
        login_btn = find_button_by_text(page, "Login")
        if login_btn:
            login_btn.invoke()
            root.update_idletasks()

    # Should call _draw_security_content and create left_panel
    assert hasattr(page, "left_panel")
    assert page.left_panel is not None


def test_draw_security_content_creates_ui(
    root, mock_sensor_manager, mock_config_manager, mock_login_manager
):
    """Test _draw_security_content creates all UI elements"""
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    # Manually call _draw_security_content
    page._draw_security_content()
    root.update_idletasks()

    # Check that UI elements are created
    assert hasattr(page, "left_panel")
    assert hasattr(page, "right_panel")
    assert hasattr(page, "control_frame")
    assert hasattr(page, "status_frame")
    assert hasattr(page, "canvas")
    assert hasattr(page, "btn_add")
    assert hasattr(page, "btn_update")
    assert hasattr(page, "btn_delete")
    assert hasattr(page, "btn_arm")
    assert hasattr(page, "btn_disarm")


def test_start_monitoring_active(
    root, mock_sensor_manager, mock_config_manager, mock_login_manager
):
    """Test _start_monitoring when active"""
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    # Set up security content
    page._draw_security_content()
    root.update_idletasks()

    # Set monitoring active
    page._monitoring_active = True

    with (
        patch.object(page, "_sync_zone_state_with_sensors") as mock_sync,
        patch.object(
            page, "_get_ui_state_snapshot", return_value=("snapshot",)
        ),
        patch.object(page, "_render_content"),
        patch.object(page, "_update_zone_status_list"),
        patch.object(page, "after", return_value=999) as mock_after,
    ):
        page._start_monitoring()
        root.update_idletasks()
        mock_sync.assert_called()
        # Should schedule next monitoring
        mock_after.assert_called()


def test_start_monitoring_inactive(
    root, mock_sensor_manager, mock_config_manager, mock_login_manager
):
    """Test _start_monitoring when inactive"""
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    page._monitoring_active = False

    with patch.object(page, "_sync_zone_state_with_sensors") as mock_sync:
        page._start_monitoring()
        root.update_idletasks()
        # Should not call sync when inactive
        mock_sync.assert_not_called()


def test_start_monitoring_widget_not_exists(
    root, mock_sensor_manager, mock_config_manager, mock_login_manager
):
    """Test _start_monitoring when widget doesn't exist"""
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    page._monitoring_active = True
    # Destroy the widget
    page.destroy()
    root.update_idletasks()

    with patch.object(page, "_sync_zone_state_with_sensors") as mock_sync:
        page._start_monitoring()
        root.update_idletasks()
        # Should not call sync when widget doesn't exist
        mock_sync.assert_not_called()


def test_sync_zone_state_with_sensors(
    root, mock_sensor_manager, mock_config_manager, mock_zone, mock_sensor
):
    """Test _sync_zone_state_with_sensors"""
    mock_sensor.is_armed.return_value = True
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    page._sync_zone_state_with_sensors()
    # Zone should be armed if any sensor is armed
    mock_zone.arm.assert_called()


def test_sync_zone_state_with_sensors_all_disarmed(
    root, mock_sensor_manager, mock_config_manager, mock_zone, mock_sensor
):
    """Test _sync_zone_state_with_sensors when all sensors disarmed"""
    mock_sensor.is_armed.return_value = False
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    page._sync_zone_state_with_sensors()
    # Zone should be disarmed if all sensors are disarmed
    mock_zone.disarm.assert_called()


def test_sync_zone_state_with_sensors_no_config(root, mock_sensor_manager):
    """Test _sync_zone_state_with_sensors without config manager"""
    page = SecurityPage(root, mock_sensor_manager, "security")
    root.update_idletasks()

    # Should not crash
    page._sync_zone_state_with_sensors()


def test_sync_zone_state_with_sensors_no_sensor_manager(
    root, mock_config_manager
):
    """Test _sync_zone_state_with_sensors without sensor manager"""
    sensor_manager = None
    page = SecurityPage(
        root,
        sensor_manager,
        "security",
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    # Should not crash
    page._sync_zone_state_with_sensors()


def test_on_canvas_ready(
    root, mock_sensor_manager, mock_config_manager, mock_login_manager
):
    """Test _on_canvas_ready schedules render"""
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    page._draw_security_content()
    root.update_idletasks()

    # Set up canvas
    page._draw_job = None

    with patch.object(page.canvas, "after", return_value=999) as mock_after:
        page._on_canvas_ready()
        root.update_idletasks()
        mock_after.assert_called()
        assert page._draw_job == 999


def test_on_canvas_ready_cancels_previous(
    root, mock_sensor_manager, mock_config_manager, mock_login_manager
):
    """Test _on_canvas_ready cancels previous job"""
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    page._draw_security_content()
    root.update_idletasks()

    page._draw_job = 123

    with (
        patch.object(page.canvas, "after_cancel") as mock_cancel,
        patch.object(page.canvas, "after", return_value=999),
    ):
        page._on_canvas_ready()
        root.update_idletasks()
        mock_cancel.assert_called_with(123)


def test_render_content(
    root, mock_sensor_manager, mock_config_manager, mock_login_manager
):
    """Test _render_content calls drawing methods"""
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    page._draw_security_content()
    root.update_idletasks()

    with (
        patch.object(page, "_draw_floor_plan") as mock_floor,
        patch.object(page, "_draw_security_zones") as mock_zones,
        patch.object(page, "_draw_sensors") as mock_sensors,
    ):
        page._render_content()
        root.update_idletasks()
        mock_floor.assert_called()
        mock_zones.assert_called()
        mock_sensors.assert_called()


def test_draw_floor_plan(
    root, mock_sensor_manager, mock_config_manager, mock_login_manager
):
    """Test _draw_floor_plan calls utility"""
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    page._draw_security_content()
    root.update_idletasks()

    with patch("core.pages.security_page.draw_floor_plan") as mock_draw:
        page._draw_floor_plan()
        mock_draw.assert_called_with(page.canvas)


def test_draw_security_zones(
    root,
    mock_sensor_manager,
    mock_config_manager,
    mock_zone,
    mock_login_manager,
):
    """Test _draw_security_zones draws zones"""
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    page._draw_security_content()
    root.update_idletasks()

    page._draw_security_zones()
    root.update_idletasks()

    # Check that zone was drawn
    assert 1 in page.zone_canvas_items


def test_draw_security_zones_armed(
    root,
    mock_sensor_manager,
    mock_config_manager,
    mock_zone,
    mock_login_manager,
):
    """Test _draw_security_zones with armed zone"""
    mock_zone.is_armed.return_value = True
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    page._draw_security_content()
    root.update_idletasks()

    page._draw_security_zones()
    root.update_idletasks()

    # Check that zone was drawn
    assert 1 in page.zone_canvas_items


def test_draw_security_zones_selected(
    root,
    mock_sensor_manager,
    mock_config_manager,
    mock_zone,
    mock_login_manager,
):
    """Test _draw_security_zones with selected zone"""
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    page._draw_security_content()
    root.update_idletasks()

    page.selected_zone_id = 1
    page._draw_security_zones()
    root.update_idletasks()

    # Check that zone was drawn
    assert 1 in page.zone_canvas_items


def test_draw_security_zones_no_config(
    root, mock_sensor_manager, mock_login_manager
):
    """Test _draw_security_zones without config manager"""
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
    )
    root.update_idletasks()

    page._draw_security_content()
    root.update_idletasks()

    # Should not crash
    page._draw_security_zones()


def test_on_canvas_click_selects_zone(
    root,
    mock_sensor_manager,
    mock_config_manager,
    mock_zone,
    mock_login_manager,
):
    """Test _on_canvas_click selects zone"""
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    page._draw_security_content()
    root.update_idletasks()

    # Draw zones first
    page._draw_security_zones()
    root.update_idletasks()

    # Create a mock event at zone center
    mock_event = Mock()
    mock_event.x = 125  # Center of zone (50+200)/2
    mock_event.y = 125  # Center of zone (50+200)/2

    with patch.object(page, "_select_zone") as mock_select:
        page._on_canvas_click(mock_event)
        root.update_idletasks()
        # Should call _select_zone
        mock_select.assert_called()


def test_on_canvas_click_deselects(
    root, mock_sensor_manager, mock_config_manager, mock_login_manager
):
    """Test _on_canvas_click deselects when clicking empty area"""
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    page._draw_security_content()
    root.update_idletasks()

    # Create a mock event at empty area
    mock_event = Mock()
    mock_event.x = 10
    mock_event.y = 10

    with patch.object(page, "_select_zone") as mock_select:
        page._on_canvas_click(mock_event)
        root.update_idletasks()
        # Should call _select_zone with None
        mock_select.assert_called_with(None)


def test_select_zone(
    root, mock_sensor_manager, mock_config_manager, mock_login_manager
):
    """Test _select_zone updates UI"""
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    page._draw_security_content()
    root.update_idletasks()

    with (
        patch.object(page, "_update_zone_selection_visual") as mock_visual,
        patch.object(page, "_update_zone_status_list") as mock_status,
        patch.object(page, "_update_button_states") as mock_buttons,
    ):
        page._select_zone(1)
        root.update_idletasks()
        assert page.selected_zone_id == 1
        mock_visual.assert_called()
        mock_status.assert_called()
        mock_buttons.assert_called()


def test_update_zone_selection_visual(
    root,
    mock_sensor_manager,
    mock_config_manager,
    mock_zone,
    mock_login_manager,
):
    """Test _update_zone_selection_visual updates canvas"""
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    page._draw_security_content()
    root.update_idletasks()

    # Draw zones first
    page._draw_security_zones()
    root.update_idletasks()

    page.selected_zone_id = 1
    page._update_zone_selection_visual()
    root.update_idletasks()


def test_draw_sensors(
    root,
    mock_sensor_manager,
    mock_config_manager,
    mock_sensor,
    mock_login_manager,
):
    """Test _draw_sensors draws sensors"""
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    page._draw_security_content()
    root.update_idletasks()

    page._draw_sensors()
    root.update_idletasks()

    # Check that sensor was drawn (canvas should have items)
    assert len(page.canvas.find_all()) > 0


def test_draw_sensors_motion_detector(
    root,
    mock_sensor_manager,
    mock_config_manager,
    mock_motion_sensor,
    mock_login_manager,
):
    """Test _draw_sensors draws motion detector sensors"""
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    page._draw_security_content()
    root.update_idletasks()

    page._draw_sensors()
    root.update_idletasks()

    # Check that sensor was drawn
    assert len(page.canvas.find_all()) > 0


def test_add_status_item(
    root, mock_sensor_manager, mock_config_manager, mock_login_manager
):
    """Test _add_status_item creates status item"""
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    page._draw_security_content()
    root.update_idletasks()

    page._add_status_item("Test Zone", "Armed", is_selected=True)
    root.update_idletasks()

    # Check that item was added
    assert len(page.status_list.winfo_children()) > 0


def test_update_zone_status_list(
    root,
    mock_sensor_manager,
    mock_config_manager,
    mock_zone,
    mock_login_manager,
):
    """Test _update_zone_status_list updates list"""
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    page._draw_security_content()
    root.update_idletasks()

    page._update_zone_status_list()
    root.update_idletasks()

    # Check that items were added
    assert len(page.status_list.winfo_children()) > 0


def test_update_zone_status_list_no_zones(
    root, mock_sensor_manager, mock_config_manager, mock_login_manager
):
    """Test _update_zone_status_list with no zones"""
    mock_config_manager.get_all_safety_zones.return_value = {}
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    page._draw_security_content()
    root.update_idletasks()

    page._update_zone_status_list()
    root.update_idletasks()

    # Should show "No zones configured" message
    children = page.status_list.winfo_children()
    assert len(children) > 0


def test_update_zone_status_list_no_config(
    root, mock_sensor_manager, mock_login_manager
):
    """Test _update_zone_status_list without config manager"""
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
    )
    root.update_idletasks()

    page._draw_security_content()
    root.update_idletasks()

    # Should not crash
    page._update_zone_status_list()


def test_update_button_states(
    root, mock_sensor_manager, mock_config_manager, mock_login_manager
):
    """Test _update_button_states updates button states"""
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    page._draw_security_content()
    root.update_idletasks()

    # Test with no selection
    page.selected_zone_id = None
    page._update_button_states()
    root.update_idletasks()

    assert page.btn_update.cget("state") == "disabled"
    assert page.btn_delete.cget("state") == "disabled"

    # Test with selection
    page.selected_zone_id = 1
    page._update_button_states()
    root.update_idletasks()

    assert page.btn_update.cget("state") == "normal"
    assert page.btn_delete.cget("state") == "normal"


def test_draw_security_zones_no_coords(
    root,
    mock_sensor_manager,
    mock_config_manager,
    mock_zone,
    mock_login_manager,
):
    """Test _draw_security_zones with zone having no coordinates"""
    mock_zone.get_coordinates.return_value = None
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    page._draw_security_content()
    root.update_idletasks()

    page._draw_security_zones()
    root.update_idletasks()

    # Zone with no coords should be skipped
    assert 1 not in page.zone_canvas_items


def test_update_zone_selection_visual_armed(
    root,
    mock_sensor_manager,
    mock_config_manager,
    mock_zone,
    mock_login_manager,
):
    """Test _update_zone_selection_visual with armed zone"""
    mock_zone.is_armed.return_value = True
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    page._draw_security_content()
    root.update_idletasks()

    # Draw zones first
    page._draw_security_zones()
    root.update_idletasks()

    page._update_zone_selection_visual()
    root.update_idletasks()


def test_draw_sensors_motion_detector_armed(
    root,
    mock_sensor_manager,
    mock_config_manager,
    mock_motion_sensor,
    mock_login_manager,
):
    """Test _draw_sensors draws armed motion detector sensors"""
    mock_motion_sensor.is_armed.return_value = True
    mock_sensor_manager.sensor_dict = {2: mock_motion_sensor}
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    page._draw_security_content()
    root.update_idletasks()

    page._draw_sensors()
    root.update_idletasks()

    # Check that sensor was drawn (canvas should have items)
    assert len(page.canvas.find_all()) > 0


def test_draw_sensors_motion_detector_with_coords(
    root,
    mock_sensor_manager,
    mock_config_manager,
    mock_motion_sensor,
    mock_login_manager,
):
    """Test _draw_sensors with motion detector having coordinate_x2/y2"""
    # Ensure coordinate_x2 and coordinate_y2 are set
    mock_motion_sensor.coordinate_x2 = 100
    mock_motion_sensor.coordinate_y2 = 100
    mock_sensor_manager.sensor_dict = {2: mock_motion_sensor}
    page = SecurityPage(
        root,
        mock_sensor_manager,
        "security",
        login_manager=mock_login_manager,
        configuration_manager=mock_config_manager,
    )
    root.update_idletasks()

    page._draw_security_content()
    root.update_idletasks()

    page._draw_sensors()
    root.update_idletasks()

    # Check that sensor was drawn
    assert len(page.canvas.find_all()) > 0
