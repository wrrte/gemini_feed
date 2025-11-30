"""
Unit tests for control_panel.py
Tests ControlPanel class with real GUI
"""

import tkinter
from unittest.mock import Mock, patch

import customtkinter as ctk
import pytest

# isort: off
from constants import (
    FUNCTION_MODE_MESSAGE1,
    FUNCTION_MODE_MESSAGE2,
    PANEL_DEFAULT_MESSAGE1,
)

# isort: on
from core.control_panel.control_panel import ControlPanel
from core.control_panel.control_panel_state_manager import ControlPanelState

# =============================================================================
# Helper Functions
# =============================================================================


def cancel_all_after(widget):
    """Cancel all pending after callbacks recursively."""
    try:
        for after_id in widget.tk.eval("after info").split():
            try:
                widget.after_cancel(after_id)
            except Exception:
                pass
    except Exception:
        pass


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def ensure_tkinter_cleanup():
    """Ensure Tkinter is properly cleaned up between tests."""
    yield
    # After each test, reset tkinter state for isolation
    try:
        if hasattr(tkinter, "_default_root") and tkinter._default_root:
            try:
                # Destroy all children first
                for widget in list(tkinter._default_root.winfo_children()):
                    try:
                        widget.destroy()
                    except Exception:
                        pass
                # Destroy the root if it exists
                if tkinter._default_root.winfo_exists():
                    tkinter._default_root.destroy()
            except Exception:
                pass
            tkinter._default_root = None
    except Exception:
        pass


@pytest.fixture
def mock_login_manager():
    """Create mock LoginManager."""
    manager = Mock()
    manager.is_logged_in_panel = False
    manager.current_user_id = None
    manager.login_trials = 0
    manager.login_panel = Mock(return_value=True)
    manager.is_login_trials_exceeded = Mock(return_value=False)
    return manager


@pytest.fixture
def mock_zone():
    """Create mock SafetyZone."""
    zone = Mock()
    zone.is_armed = Mock(return_value=False)
    return zone


@pytest.fixture
def mock_configuration_manager(mock_zone):
    """Create mock ConfigurationManager."""
    manager = Mock()
    manager.safety_zones = {
        1: mock_zone,
        2: mock_zone,
        3: mock_zone,
        4: mock_zone,
    }
    manager.change_to_safehome_mode = Mock(return_value=True)
    manager.arm_safety_zone = Mock(return_value=True)
    manager.disarm_safety_zone = Mock(return_value=True)
    return manager


@pytest.fixture
def mock_alarm_manager():
    """Create mock AlarmManager."""
    manager = Mock()
    manager.is_ringing = Mock(return_value=False)
    manager.stop_alarm = Mock()
    return manager


@pytest.fixture
def mock_sensor_manager():
    """Create mock SensorManager."""
    manager = Mock()
    manager.if_intrusion_detected = Mock(return_value=False)
    return manager


@pytest.fixture
def mock_callbacks():
    """Create mock callback functions."""
    return {
        "turn_system_on": Mock(return_value=True),
        "turn_system_off": Mock(return_value=True),
        "set_reset_database": Mock(),
        "external_call": Mock(return_value=["123-456-7890", "098-765-4321"]),
    }


@pytest.fixture
def control_panel(
    mock_login_manager, mock_configuration_manager, mock_callbacks
):
    """Create a ControlPanel instance for testing with real GUI (hidden)."""
    # Patch CTk.__init__ to immediately withdraw after creation
    original_ctk_init = ctk.CTk.__init__

    def patched_ctk_init(self, *args, **kwargs):
        original_ctk_init(self, *args, **kwargs)
        self.withdraw()

    with patch.object(ctk.CTk, "__init__", patched_ctk_init):
        panel = ControlPanel(
            turn_system_on=mock_callbacks["turn_system_on"],
            turn_system_off=mock_callbacks["turn_system_off"],
            set_reset_database=mock_callbacks["set_reset_database"],
            external_call=mock_callbacks["external_call"],
            login_manager=mock_login_manager,
            configuration_manager=mock_configuration_manager,
        )
        panel.update_idletasks()

    yield panel

    # Cleanup - cancel callbacks and destroy
    try:
        cancel_all_after(panel)
        panel.withdraw()
        panel.destroy()
    except Exception:
        pass


# ============================================================================
# State Transition Tests
# ============================================================================


def test_change_state_to_initialized(control_panel):
    """Test state change to INITIALIZED."""
    control_panel.state_manager.change_state_to(ControlPanelState.INITIALIZED)

    assert (
        control_panel.state_manager.panel_state
        == ControlPanelState.INITIALIZED
    )
    assert control_panel.input_handler.digit_input == []
    assert control_panel.input_handler.panel_id_input == ""
    assert control_panel.input_handler.new_password_temp == ""
    # Message includes login status prefix
    assert PANEL_DEFAULT_MESSAGE1 in control_panel.ui.short_message1
    assert control_panel.ui.short_message1.startswith("(unauthorized)")


def test_change_state_to_offline(control_panel):
    """Test state change to OFFLINE."""
    control_panel.powered = True
    control_panel.state_manager.change_state_to(ControlPanelState.OFFLINE)

    assert control_panel.state_manager.panel_state == ControlPanelState.OFFLINE
    assert control_panel.powered is False
    assert control_panel.input_handler.digit_input == []
    assert control_panel.input_handler.panel_id_input == ""
    # OFFLINE state shows "turn-off" with login prefix
    assert "turn-off" in control_panel.ui.short_message1
    assert control_panel.ui.short_message2 == ""


def test_change_state_to_function_mode(control_panel):
    """Test state change to FUNCTION_MODE."""
    control_panel.state_manager.change_state_to(
        ControlPanelState.FUNCTION_MODE
    )

    assert (
        control_panel.state_manager.panel_state
        == ControlPanelState.FUNCTION_MODE
    )
    # Message includes login status prefix
    assert FUNCTION_MODE_MESSAGE1 in control_panel.ui.short_message1
    assert FUNCTION_MODE_MESSAGE2 in control_panel.ui.short_message2


def test_change_state_to_panel_id_input(control_panel):
    """Test state change to PANEL_ID_INPUT."""
    control_panel.input_handler.digit_input = [1, 2, 3]
    control_panel.state_manager.change_state_to(
        ControlPanelState.PANEL_ID_INPUT
    )

    assert (
        control_panel.state_manager.panel_state
        == ControlPanelState.PANEL_ID_INPUT
    )
    assert control_panel.input_handler.digit_input == []
    assert control_panel.input_handler.panel_id_input == ""
    assert "Enter panel ID" in control_panel.ui.short_message1


def test_change_state_to_digit_input(control_panel):
    """Test state change to DIGIT_INPUT."""
    control_panel.state_manager.change_state_to(ControlPanelState.DIGIT_INPUT)

    assert (
        control_panel.state_manager.panel_state
        == ControlPanelState.DIGIT_INPUT
    )
    assert "password" in control_panel.ui.short_message1.lower()


def test_change_state_to_password_change_input_1(control_panel):
    """Test state change to MASTER_PASSWORD_CHANGE_INPUT_1."""
    control_panel.input_handler.digit_input = [1, 2, 3, 4]
    control_panel.input_handler.new_password_temp = "test"

    control_panel.state_manager.change_state_to(
        ControlPanelState.MASTER_PASSWORD_CHANGE_INPUT_1
    )

    assert (
        control_panel.state_manager.panel_state
        == ControlPanelState.MASTER_PASSWORD_CHANGE_INPUT_1
    )
    assert control_panel.input_handler.digit_input == []
    assert control_panel.input_handler.new_password_temp == ""


def test_change_state_to_password_change_input_2(control_panel):
    """Test state change to MASTER_PASSWORD_CHANGE_INPUT_2."""
    control_panel.input_handler.new_password_temp = "1234"
    control_panel.input_handler.digit_input = [1, 2, 3, 4]

    control_panel.state_manager.change_state_to(
        ControlPanelState.MASTER_PASSWORD_CHANGE_INPUT_2
    )

    assert (
        control_panel.state_manager.panel_state
        == ControlPanelState.MASTER_PASSWORD_CHANGE_INPUT_2
    )
    assert control_panel.input_handler.digit_input == []
    assert (
        control_panel.input_handler.new_password_temp == "1234"
    )  # Should be preserved


def test_change_state_to_locked(control_panel):
    """Test state change to LOCKED."""
    with patch.object(control_panel.state_manager, "_update_lock_timer"):
        control_panel.state_manager.change_state_to(ControlPanelState.LOCKED)

        assert (
            control_panel.state_manager.panel_state == ControlPanelState.LOCKED
        )
        assert control_panel.state_manager.lock_start_time is not None


def test_change_state_with_custom_messages(control_panel):
    """Test state change with custom messages."""
    control_panel.state_manager.change_state_to(
        ControlPanelState.INITIALIZED,
        custom_message1="Custom Message 1",
        custom_message2="Custom Message 2",
    )

    # Custom message includes login status prefix
    assert "Custom Message 1" in control_panel.ui.short_message1
    assert control_panel.ui.short_message1.startswith("(unauthorized)")
    assert ": Custom Message 2" in control_panel.ui.short_message2


# ============================================================================
# Authorization Tests
# ============================================================================


def test_verify_login_master_success(control_panel):
    """Test verify login for master user."""
    # Set mock login state directly
    control_panel.login_manager.is_logged_in_panel = True
    control_panel.login_manager.current_user_id = "master"

    assert control_panel._verify_login("master") is True


def test_verify_login_master_fail_not_logged_in(control_panel):
    """Test verify login fails when not logged in."""
    assert control_panel._verify_login("master") is False


def test_verify_login_master_fail_wrong_user(control_panel):
    """Test verify login fails when logged in as different user."""
    control_panel.login_manager.is_logged_in_panel = True
    control_panel.login_manager.current_user_id = "guest"

    assert control_panel._verify_login("master") is False


def test_check_authorization_master_success(control_panel):
    """Test check authorization for master user."""
    control_panel.login_manager.is_logged_in_panel = True
    control_panel.login_manager.current_user_id = "master"

    assert control_panel._check_authorization("master") is True


def test_check_authorization_master_fail(control_panel):
    """Test check authorization fails and shows error message."""
    result = control_panel._check_authorization("master")

    assert result is False
    assert "Unauthorized" in control_panel.ui.short_message1
    assert "master" in control_panel.ui.short_message2.lower()


def test_check_authorization_any_with_master(control_panel):
    """Test check authorization 'any' with master login."""
    control_panel.login_manager.is_logged_in_panel = True
    control_panel.login_manager.current_user_id = "master"

    assert control_panel._check_authorization("any") is True


def test_check_authorization_any_with_guest(control_panel):
    """Test check authorization 'any' with guest login."""
    control_panel.login_manager.is_logged_in_panel = True
    control_panel.login_manager.current_user_id = "guest"

    assert control_panel._check_authorization("any") is True


def test_check_authorization_any_fail(control_panel):
    """Test check authorization 'any' fails when not logged in."""
    result = control_panel._check_authorization("any")

    assert result is False
    assert "Unauthorized" in control_panel.ui.short_message1


# ============================================================================
# Zone Navigation Tests
# ============================================================================


def test_get_sorted_zone_ids(control_panel):
    """Test getting sorted zone IDs."""
    zone_ids = control_panel._get_sorted_zone_ids()

    # init_data.sql creates 4 zones (1, 2, 3, 4)
    assert zone_ids == [1, 2, 3, 4]


def test_navigate_to_previous_zone_from_first(control_panel):
    """Test navigating to previous zone from first zone (wraps to last)."""
    control_panel.ui.security_zone_number = 1

    control_panel._navigate_to_previous_zone()

    # Wraps to last zone (4)
    assert control_panel.ui.security_zone_number == 4


def test_navigate_to_previous_zone_from_second(control_panel):
    """Test navigating to previous zone from second zone."""
    control_panel.ui.security_zone_number = 3

    control_panel._navigate_to_previous_zone()

    assert control_panel.ui.security_zone_number == 2


def test_navigate_to_previous_zone_when_none(control_panel):
    """Test navigating to previous zone when current is None."""
    control_panel.ui.security_zone_number = None

    control_panel._navigate_to_previous_zone()

    # When None, sets to first zone
    assert control_panel.ui.security_zone_number == 1


def test_navigate_to_next_zone_from_last(control_panel):
    """Test navigating to next zone from last zone (wraps to first)."""
    control_panel.ui.security_zone_number = 4

    control_panel._navigate_to_next_zone()

    # Wraps to first zone (1)
    assert control_panel.ui.security_zone_number == 1


def test_navigate_to_next_zone_from_first(control_panel):
    """Test navigating to next zone from first zone."""
    control_panel.ui.security_zone_number = 2

    control_panel._navigate_to_next_zone()

    assert control_panel.ui.security_zone_number == 3


def test_navigate_to_next_zone_when_none(control_panel):
    """Test navigating to next zone when current is None."""
    control_panel.ui.security_zone_number = None

    control_panel._navigate_to_next_zone()

    # When None, sets to first zone
    assert control_panel.ui.security_zone_number == 1


def test_navigate_with_empty_zones(control_panel):
    """Test zone navigation with no zones."""
    control_panel.configuration_manager.safety_zones = {}
    control_panel.ui.security_zone_number = None

    control_panel._navigate_to_next_zone()

    assert control_panel.ui.security_zone_number is None


# ============================================================================
# Display Message Tests
# ============================================================================


def test_set_display_short_message1(control_panel):
    """Test setting first display message."""
    control_panel.ui.set_display_short_message1("Message 1", "")

    assert control_panel.ui.short_message1 == "Message 1"


def test_set_display_short_message2(control_panel):
    """Test setting second display message."""
    control_panel.ui.set_display_short_message2("Message 2")

    assert ": Message 2" in control_panel.ui.short_message2


# ============================================================================
# Button Handler Tests
# ============================================================================


def test_handle_button_press_locked_state(control_panel):
    """Test button press is ignored when panel is locked."""
    control_panel.state_manager.panel_state = ControlPanelState.LOCKED
    original_state = control_panel.state_manager.panel_state

    control_panel.input_handler.handle_button_press("1")

    assert control_panel.state_manager.panel_state == original_state


def test_handle_button_press_back_to_init(control_panel):
    """Test # button returns to initialized state."""
    control_panel.state_manager.panel_state = ControlPanelState.FUNCTION_MODE
    control_panel.input_handler.digit_input = [1, 2, 3]

    control_panel.input_handler.handle_button_press("#")

    assert (
        control_panel.state_manager.panel_state
        == ControlPanelState.INITIALIZED
    )
    assert control_panel.input_handler.digit_input == []


def test_handle_button_press_function_mode_entry(control_panel):
    """Test button 6 enters function mode."""
    control_panel.state_manager.panel_state = ControlPanelState.INITIALIZED

    control_panel.input_handler.handle_button_press("6")

    assert (
        control_panel.state_manager.panel_state
        == ControlPanelState.FUNCTION_MODE
    )


def test_handle_button_press_panic(control_panel, mock_callbacks):
    """Test panic button triggers external call."""
    # Turn on panel first (panic button only works when panel is on)
    control_panel.state_manager.change_state_to(ControlPanelState.INITIALIZED)

    with patch.object(control_panel, "_panic_button_press") as mock_panic:
        control_panel.input_handler.handle_button_press("panic")

        mock_panic.assert_called_once()


# ============================================================================
# Login Tests
# ============================================================================


def test_handle_panel_login_success_master(control_panel):
    """Test successful panel login for master."""
    control_panel.input_handler.panel_id_input = "master"
    control_panel.input_handler.digit_input = [1, 2, 3, 4]
    control_panel.login_manager.login_panel.return_value = True

    result = control_panel.input_handler._handle_panel_login()

    assert result is True
    control_panel.login_manager.login_panel.assert_called_with(
        "master", "1234"
    )
    assert control_panel.input_handler.digit_input == []


def test_handle_panel_login_fail_wrong_password(control_panel):
    """Test failed panel login with wrong password."""
    control_panel.input_handler.panel_id_input = "master"
    control_panel.input_handler.digit_input = [0, 0, 0, 0]
    control_panel.login_manager.login_panel.return_value = False

    result = control_panel.input_handler._handle_panel_login()

    assert result is False
    assert "Login failed" in control_panel.ui.short_message1


def test_handle_panel_login_fail_insufficient_digits(control_panel):
    """Test login fails with insufficient digits."""
    control_panel.input_handler.panel_id_input = "master"
    control_panel.input_handler.digit_input = [1, 2]

    result = control_panel.input_handler._handle_panel_login()

    assert result is False


def test_handle_panel_login_locks_after_max_trials(control_panel):
    """Test panel locks after maximum login trials."""
    control_panel.input_handler.panel_id_input = "master"
    control_panel.login_manager.login_panel.return_value = False
    control_panel.login_manager.is_login_trials_exceeded.return_value = True

    control_panel.input_handler.digit_input = [0, 0, 0, 0]
    control_panel.input_handler._handle_panel_login()

    assert control_panel.state_manager.panel_state == ControlPanelState.LOCKED


# ============================================================================
# Password Change Tests
# ============================================================================


def test_password_change_first_input(control_panel):
    """Test first password input during password change."""
    control_panel.state_manager.panel_state = (
        ControlPanelState.MASTER_PASSWORD_CHANGE_INPUT_1
    )

    handler = control_panel.input_handler
    for digit in ["5", "6", "7", "8"]:
        handler._handle_master_password_change_button_press(digit)

    assert (
        control_panel.state_manager.panel_state
        == ControlPanelState.MASTER_PASSWORD_CHANGE_INPUT_2
    )
    assert control_panel.input_handler.new_password_temp == "5678"
    assert control_panel.input_handler.digit_input == []


def test_password_change_matching_passwords(control_panel):
    """Test password change with matching passwords."""
    control_panel.state_manager.panel_state = (
        ControlPanelState.MASTER_PASSWORD_CHANGE_INPUT_1
    )
    control_panel.input_handler.new_password_temp = ""

    handler = control_panel.input_handler
    # First password
    for digit in ["1", "2", "3", "4"]:
        handler._handle_master_password_change_button_press(digit)

    # Second password (matching)
    for digit in ["1", "2", "3", "4"]:
        handler._handle_master_password_change_button_press(digit)

    assert "Password changed" in control_panel.ui.short_message1


def test_password_change_non_matching_passwords(control_panel):
    """Test password change with non-matching passwords."""
    control_panel.state_manager.panel_state = (
        ControlPanelState.MASTER_PASSWORD_CHANGE_INPUT_1
    )
    control_panel.input_handler.new_password_temp = ""

    handler = control_panel.input_handler
    # First password
    for digit in ["1", "2", "3", "4"]:
        handler._handle_master_password_change_button_press(digit)

    # Second password (different)
    for digit in ["5", "6", "7", "8"]:
        handler._handle_master_password_change_button_press(digit)

    assert "mismatch" in control_panel.ui.short_message1.lower()


def test_password_change_ignores_non_digit(control_panel):
    """Test password change ignores non-digit buttons."""
    control_panel.state_manager.panel_state = (
        ControlPanelState.MASTER_PASSWORD_CHANGE_INPUT_1
    )

    handler = control_panel.input_handler
    handler._handle_master_password_change_button_press("*")

    assert len(handler.digit_input) == 0


# ============================================================================
# Panel Power Tests
# ============================================================================


def test_start_lock_timer(control_panel):
    """Test starting panel lock timer."""
    control_panel.state_manager.start_lock_timer()

    assert control_panel.state_manager.panel_state == ControlPanelState.LOCKED
    assert control_panel.state_manager.lock_start_time is not None


def test_unlock_panel(control_panel):
    """Test unlocking panel."""
    control_panel.state_manager.panel_state = ControlPanelState.LOCKED
    control_panel.state_manager.lock_start_time = 12345
    control_panel.state_manager.lock_timer_id = Mock()

    with patch.object(control_panel, "after_cancel"):
        control_panel.state_manager.unlock_panel()

    assert (
        control_panel.state_manager.panel_state
        == ControlPanelState.INITIALIZED
    )
    assert control_panel.state_manager.lock_start_time is None
    assert control_panel.state_manager.lock_timer_id is None


# ============================================================================
# Helper Method Tests
# ============================================================================


def test_panel_state_initialization(control_panel):
    """Test panel state is properly initialized."""
    # Panel starts in OFFLINE state
    assert control_panel.state_manager.panel_state == ControlPanelState.OFFLINE
    assert control_panel.powered is False
    assert control_panel.input_handler.digit_input == []
    assert control_panel.input_handler.new_password_temp == ""


# ============================================================================
# set_managers Tests
# ============================================================================


def test_set_managers(control_panel, mock_alarm_manager, mock_sensor_manager):
    """Test set_managers updates all manager references."""
    new_login_manager = Mock()
    new_config_manager = Mock()

    control_panel.set_managers(
        login_manager=new_login_manager,
        configuration_manager=new_config_manager,
        alarm_manager=mock_alarm_manager,
        sensor_manager=mock_sensor_manager,
    )

    assert control_panel.login_manager == new_login_manager
    assert control_panel.configuration_manager == new_config_manager
    assert control_panel.alarm_manager == mock_alarm_manager
    assert control_panel.sensor_manager == mock_sensor_manager


def test_set_managers_without_optional(control_panel):
    """Test set_managers without optional managers."""
    new_login_manager = Mock()
    new_config_manager = Mock()

    control_panel.set_managers(
        login_manager=new_login_manager,
        configuration_manager=new_config_manager,
    )

    assert control_panel.login_manager == new_login_manager
    assert control_panel.configuration_manager == new_config_manager
    assert control_panel.alarm_manager is None
    assert control_panel.sensor_manager is None


# ============================================================================
# start_count_down_for_external_call Tests
# ============================================================================


def test_start_count_down_for_external_call(control_panel):
    """Test start_count_down_for_external_call calls state manager."""
    with patch.object(
        control_panel.state_manager, "start_count_down_for_external_call"
    ) as mock_countdown:
        control_panel.start_count_down_for_external_call()
        mock_countdown.assert_called_once()


# ============================================================================
# _turn_panel_on Tests
# ============================================================================


def test_turn_panel_on_when_already_powered(control_panel):
    """Test _turn_panel_on returns early when already powered."""
    control_panel.powered = True

    control_panel._turn_panel_on()

    # turn_system_on callback should not be called
    control_panel.turn_system_on.assert_not_called()


def test_turn_panel_on_success(control_panel, mock_zone):
    """Test _turn_panel_on successful startup."""
    control_panel.powered = False
    control_panel.turn_system_on.return_value = True

    control_panel._turn_panel_on()
    control_panel.update_idletasks()

    assert control_panel.powered is True
    control_panel.turn_system_on.assert_called_once()


def test_turn_panel_on_failure(control_panel):
    """Test _turn_panel_on when turn_system_on returns False."""
    control_panel.powered = False
    control_panel.turn_system_on.return_value = False

    control_panel._turn_panel_on()
    control_panel.update_idletasks()

    assert control_panel.powered is False
    # Check that failure message is displayed
    assert "failed" in control_panel.ui.short_message1.lower()


def test_turn_panel_on_exception(control_panel):
    """Test _turn_panel_on when turn_system_on raises exception."""
    control_panel.powered = False
    control_panel.turn_system_on.side_effect = Exception("Test error")

    control_panel._turn_panel_on()
    control_panel.update_idletasks()

    assert control_panel.powered is False
    # Check that error message is displayed
    assert "failed" in control_panel.ui.short_message1.lower()


def test_turn_panel_on_sets_zone_number(control_panel, mock_zone):
    """Test _turn_panel_on sets security zone number."""
    control_panel.powered = False
    control_panel.turn_system_on.return_value = True
    control_panel.ui.security_zone_number = None

    control_panel._turn_panel_on()
    control_panel.update_idletasks()

    # Should set zone number from configuration (first zone is 1)
    assert control_panel.ui.security_zone_number == 1


def test_turn_panel_on_sets_armed_led(control_panel, mock_zone):
    """Test _turn_panel_on sets armed LED based on zone state."""
    control_panel.powered = False
    control_panel.turn_system_on.return_value = True
    control_panel.ui.security_zone_number = 1
    mock_zone.is_armed.return_value = True

    control_panel._turn_panel_on()
    control_panel.update_idletasks()

    # LED state verified through zone.is_armed being called
    mock_zone.is_armed.assert_called()


# ============================================================================
# sync_system_state_loop Tests
# ============================================================================


def test_sync_system_state_loop_when_not_powered(control_panel):
    """Test sync_system_state_loop returns early when not powered."""
    control_panel.powered = False

    with patch.object(control_panel, "_sync_armed_led") as mock_sync:
        control_panel.sync_system_state_loop()
        mock_sync.assert_not_called()


def test_sync_system_state_loop_when_powered(control_panel):
    """Test sync_system_state_loop syncs state when powered."""
    control_panel.powered = True

    with (
        patch.object(control_panel, "_sync_armed_led") as mock_sync_led,
        patch.object(
            control_panel, "_auto_stop_alarm_if_all_released"
        ) as mock_auto_stop,
        patch.object(control_panel, "after") as mock_after,
    ):
        control_panel.sync_system_state_loop()

        mock_sync_led.assert_called_once()
        mock_auto_stop.assert_called_once()
        # Should schedule next sync
        mock_after.assert_called()


# ============================================================================
# _sync_armed_led Tests
# ============================================================================


def test_sync_armed_led_with_zone(control_panel, mock_zone):
    """Test _sync_armed_led updates LED based on zone state."""
    control_panel.ui.security_zone_number = 1
    mock_zone.is_armed.return_value = True

    control_panel._sync_armed_led()

    # Verify zone.is_armed was called to check state
    mock_zone.is_armed.assert_called()


def test_sync_armed_led_no_zone_selected(control_panel):
    """Test _sync_armed_led does nothing when no zone selected."""
    control_panel.ui.security_zone_number = None

    # Should not raise any exception
    control_panel._sync_armed_led()


def test_sync_armed_led_no_config_manager(control_panel):
    """Test _sync_armed_led does nothing when no configuration manager."""
    control_panel.ui.security_zone_number = 1
    control_panel.configuration_manager = None

    # Should not raise any exception
    control_panel._sync_armed_led()


def test_sync_armed_led_zone_not_found(control_panel):
    """Test _sync_armed_led does nothing when zone not found."""
    control_panel.ui.security_zone_number = 999  # Non-existent zone

    # Should not raise any exception
    control_panel._sync_armed_led()


# ============================================================================
# _auto_stop_alarm_if_all_released Tests
# ============================================================================


def test_auto_stop_alarm_no_managers(control_panel):
    """Test _auto_stop_alarm_if_all_released does nothing without managers."""
    control_panel.alarm_manager = None
    control_panel.sensor_manager = None

    with patch.object(
        control_panel.state_manager, "change_state_to"
    ) as mock_change:
        control_panel._auto_stop_alarm_if_all_released()
        mock_change.assert_not_called()


def test_auto_stop_alarm_no_alarm_manager(control_panel, mock_sensor_manager):
    """Test _auto_stop_alarm does nothing without alarm manager."""
    control_panel.alarm_manager = None
    control_panel.sensor_manager = mock_sensor_manager

    with patch.object(
        control_panel.state_manager, "change_state_to"
    ) as mock_change:
        control_panel._auto_stop_alarm_if_all_released()
        mock_change.assert_not_called()


def test_auto_stop_alarm_no_sensor_manager(control_panel, mock_alarm_manager):
    """Test _auto_stop_alarm does nothing without sensor manager."""
    control_panel.alarm_manager = mock_alarm_manager
    control_panel.sensor_manager = None

    with patch.object(
        control_panel.state_manager, "change_state_to"
    ) as mock_change:
        control_panel._auto_stop_alarm_if_all_released()
        mock_change.assert_not_called()


def test_auto_stop_alarm_when_not_ringing(
    control_panel, mock_alarm_manager, mock_sensor_manager
):
    """Test _auto_stop_alarm does nothing when alarm not ringing."""
    control_panel.alarm_manager = mock_alarm_manager
    control_panel.sensor_manager = mock_sensor_manager
    mock_alarm_manager.is_ringing.return_value = False

    with patch.object(
        control_panel.state_manager, "change_state_to"
    ) as mock_change:
        control_panel._auto_stop_alarm_if_all_released()
        mock_change.assert_not_called()


def test_auto_stop_alarm_when_intrusion_detected(
    control_panel, mock_alarm_manager, mock_sensor_manager
):
    """Test _auto_stop_alarm does nothing when intrusion detected."""
    control_panel.alarm_manager = mock_alarm_manager
    control_panel.sensor_manager = mock_sensor_manager
    mock_alarm_manager.is_ringing.return_value = True
    mock_sensor_manager.if_intrusion_detected.return_value = True

    with patch.object(
        control_panel.state_manager, "change_state_to"
    ) as mock_change:
        control_panel._auto_stop_alarm_if_all_released()
        mock_change.assert_not_called()


def test_auto_stop_alarm_stops_when_all_released(
    control_panel, mock_alarm_manager, mock_sensor_manager
):
    """Test _auto_stop_alarm stops alarm when all sensors released."""
    control_panel.alarm_manager = mock_alarm_manager
    control_panel.sensor_manager = mock_sensor_manager
    mock_alarm_manager.is_ringing.return_value = True
    mock_sensor_manager.if_intrusion_detected.return_value = False

    with patch.object(
        control_panel.state_manager, "change_state_to"
    ) as mock_change:
        control_panel._auto_stop_alarm_if_all_released()
        mock_change.assert_called_once_with(ControlPanelState.INITIALIZED)


# ============================================================================
# _turn_panel_off Tests
# ============================================================================


def test_turn_panel_off_when_not_powered(control_panel):
    """Test _turn_panel_off returns early when not powered."""
    control_panel.powered = False

    control_panel._turn_panel_off()

    control_panel.turn_system_off.assert_not_called()


def test_turn_panel_off_success(control_panel):
    """Test _turn_panel_off successful shutdown."""
    control_panel.powered = True
    control_panel.turn_system_off.return_value = True

    # Capture and execute the after callback to cover the success path
    def capture_after(delay, callback):
        callback()
        return 123

    with patch.object(control_panel, "after") as mock_after:
        mock_after.side_effect = capture_after
        control_panel._turn_panel_off()

    # Should transition to OFFLINE state
    assert control_panel.state_manager.panel_state == ControlPanelState.OFFLINE


def test_turn_panel_off_failure(control_panel):
    """Test _turn_panel_off when turn_system_off returns False."""
    control_panel.powered = True
    control_panel.turn_system_off.return_value = False

    # Capture the after callback and execute it
    def capture_after(delay, callback):
        callback()
        return 123

    with patch.object(control_panel, "after") as mock_after:
        mock_after.side_effect = capture_after
        control_panel._turn_panel_off()

    # Should show failure message
    assert "failed" in control_panel.ui.short_message1.lower()


def test_turn_panel_off_exception(control_panel):
    """Test _turn_panel_off when turn_system_off raises exception."""
    control_panel.powered = True
    control_panel.turn_system_off.side_effect = Exception("Test error")

    # Capture the after callback and execute it
    def capture_after(delay, callback):
        callback()
        return 123

    with patch.object(control_panel, "after") as mock_after:
        mock_after.side_effect = capture_after
        control_panel._turn_panel_off()

    # Should show failure message
    assert "failed" in control_panel.ui.short_message1.lower()


# ============================================================================
# _reset_panel Tests
# ============================================================================


def test_reset_panel(control_panel):
    """Test _reset_panel turns off and restarts panel."""
    control_panel.powered = True

    with (
        patch.object(control_panel, "_turn_panel_off") as mock_off,
        patch.object(control_panel, "_turn_panel_on"),
        patch.object(control_panel, "after") as mock_after,
    ):
        mock_after.return_value = 123
        control_panel._reset_panel()

        mock_off.assert_called_once()
        # After callback should be scheduled for restart
        mock_after.assert_called()


def test_reset_panel_sets_reset_database(control_panel):
    """Test _reset_panel sets reset database flag."""
    control_panel.powered = True

    # Capture and execute all after callbacks
    callbacks = []

    def capture_after(delay, callback):
        callbacks.append((delay, callback))
        return len(callbacks)

    with (
        patch.object(control_panel, "_turn_panel_off"),
        patch.object(control_panel, "after") as mock_after,
    ):
        mock_after.side_effect = capture_after
        control_panel._reset_panel()

    # Execute restart callback (should be the last one for restart)
    for delay, callback in callbacks:
        if delay > 100:  # The restart callback has a longer delay
            callback()
            break

    control_panel.set_reset_database.assert_called_with(True)


# ============================================================================
# _panic_button_press Tests
# ============================================================================


def test_panic_button_press(control_panel):
    """Test _panic_button_press shows message and makes calls."""
    with patch.object(control_panel, "after") as mock_after:
        mock_after.return_value = 123
        control_panel._panic_button_press()
        mock_after.assert_called()

    # Check emergency message is displayed
    assert "Emergency" in control_panel.ui.short_message1


def test_panic_button_press_success(control_panel):
    """Test _panic_button_press when external call succeeds."""
    control_panel.external_call.return_value = ["123-456-7890"]

    # Capture and execute make_calls callback
    callbacks = []

    def capture_after(delay, callback):
        callbacks.append((delay, callback))
        return len(callbacks)

    with patch.object(control_panel, "after") as mock_after:
        mock_after.side_effect = capture_after
        control_panel._panic_button_press()

    # Execute the make_calls callback
    for delay, callback in callbacks:
        if delay > 0:
            callback()
            break

    control_panel.external_call.assert_called_once()


def test_panic_button_press_failure(control_panel):
    """Test _panic_button_press when external call fails."""
    control_panel.external_call.return_value = []

    # Capture and execute make_calls callback
    callbacks = []

    def capture_after(delay, callback):
        callbacks.append((delay, callback))
        return len(callbacks)

    with patch.object(control_panel, "after") as mock_after:
        mock_after.side_effect = capture_after
        control_panel._panic_button_press()

    # Execute the make_calls callback
    for delay, callback in callbacks:
        if delay > 0:
            callback()
            break

    # Should show failure message
    assert "failed" in control_panel.ui.short_message1.lower()


# ============================================================================
# _verify_login Additional Tests
# ============================================================================


def test_verify_login_no_login_manager(control_panel):
    """Test _verify_login returns False when no login manager."""
    control_panel.login_manager = None

    assert control_panel._verify_login("master") is False


def test_verify_login_guest_success(control_panel, mock_login_manager):
    """Test _verify_login for guest user."""
    mock_login_manager.is_logged_in_panel = True
    mock_login_manager.current_user_id = "guest"

    assert control_panel._verify_login("guest") is True


def test_verify_login_guest_fail_wrong_user(control_panel, mock_login_manager):
    """Test _verify_login for guest fails when logged in as master."""
    mock_login_manager.is_logged_in_panel = True
    mock_login_manager.current_user_id = "master"

    assert control_panel._verify_login("guest") is False


def test_verify_login_invalid_id(control_panel, mock_login_manager):
    """Test _verify_login returns False for invalid ID."""
    mock_login_manager.is_logged_in_panel = True
    mock_login_manager.current_user_id = "master"

    # Call with invalid id (not "master" or "guest")
    # The function only handles "master" and "guest", so it returns False
    assert control_panel._verify_login("admin") is False


# ============================================================================
# Zone Navigation Additional Tests
# ============================================================================


def test_navigate_to_previous_zone_not_in_list(control_panel):
    """Test navigating to previous zone when current zone not in list."""
    control_panel.ui.security_zone_number = 999  # Not in list

    control_panel._navigate_to_previous_zone()

    # Should set to first zone
    assert control_panel.ui.security_zone_number == 1


def test_navigate_to_next_zone_not_in_list(control_panel):
    """Test navigating to next zone when current zone not in list."""
    control_panel.ui.security_zone_number = 999  # Not in list

    control_panel._navigate_to_next_zone()

    # Should set to first zone
    assert control_panel.ui.security_zone_number == 1


def test_navigate_to_previous_with_empty_zones(control_panel):
    """Test _navigate_to_previous_zone with no zones."""
    control_panel.configuration_manager.safety_zones = {}
    control_panel.ui.security_zone_number = None

    control_panel._navigate_to_previous_zone()

    assert control_panel.ui.security_zone_number is None
