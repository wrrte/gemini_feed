import os
from unittest.mock import Mock, patch

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
from manager.configuration_manager import ConfigurationManager
from manager.login_manager import LoginManager
from manager.storage_manager import StorageManager

current_dir = os.path.dirname(os.path.abspath(__file__))
db_dir = os.path.abspath(os.path.join(current_dir, "../../database"))


@pytest.fixture(autouse=True)
def reset_singleton_storage_manager():
    """
    Reset the singleton instance of StorageManager before and after each test.
    This prevents interference between tests.
    """
    # Setup: Reset instance
    StorageManager._instance = None

    yield

    # Teardown: Clean up database connection and reset instance
    if StorageManager._instance:
        if hasattr(StorageManager._instance, "connection"):
            if StorageManager._instance.connection:
                StorageManager._instance.connection.close()

    StorageManager._instance = None

    # Delete test database file
    test_db_path = os.path.join(db_dir, "safehome_test.db")
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture
def storage_manager():
    """Create a StorageManager with test database."""
    return StorageManager(db_file_name="safehome_test.db", reset_database=True)


@pytest.fixture
def login_manager(storage_manager):
    """Create a LoginManager with test users."""
    return LoginManager(storage_manager=storage_manager)


@pytest.fixture
def configuration_manager(storage_manager):
    """Create a ConfigurationManager."""
    configuration_manager = ConfigurationManager(
        storage_manager=storage_manager
    )
    return configuration_manager


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
def control_panel(login_manager, configuration_manager, mock_callbacks):
    """Create a ControlPanel instance for testing (Unit Test - UI Mocked)."""
    # Mock ui.draw_page to skip UI creation
    with patch("core.control_panel.control_panel_ui.ControlPanelUI.draw_page"):
        panel = ControlPanel(
            turn_system_on=mock_callbacks["turn_system_on"],
            turn_system_off=mock_callbacks["turn_system_off"],
            set_reset_database=mock_callbacks["set_reset_database"],
            external_call=mock_callbacks["external_call"],
            login_manager=login_manager,
            configuration_manager=configuration_manager,
        )

        # Mock only UI widget elements (not business logic methods)
        panel.ui.display_number = Mock()
        panel.ui.display_number.configure = Mock()
        panel.ui.display_number.delete = Mock()
        panel.ui.display_number.insert = Mock()

        panel.ui.display_away = Mock()
        panel.ui.display_away.configure = Mock()

        panel.ui.display_home = Mock()
        panel.ui.display_home.configure = Mock()

        panel.ui.display_not_ready = Mock()
        panel.ui.display_not_ready.configure = Mock()

        panel.ui.display_text = Mock()
        panel.ui.display_text.delete = Mock()
        panel.ui.display_text.insert = Mock()

        panel.ui.led_armed = Mock()
        panel.ui.led_armed.configure = Mock()

        panel.ui.led_power = Mock()
        panel.ui.led_power.configure = Mock()

        # Mock Tkinter timing methods only
        panel.after = Mock()
        panel.after_cancel = Mock()

        return panel


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
    control_panel.login_manager.login_panel("master", "1234")

    assert control_panel._verify_login("master") is True


def test_verify_login_master_fail_not_logged_in(control_panel):
    """Test verify login fails when not logged in."""
    assert control_panel._verify_login("master") is False


def test_verify_login_master_fail_wrong_user(control_panel):
    """Test verify login fails when logged in as different user."""
    control_panel.login_manager.login_panel("guest", None)

    assert control_panel._verify_login("master") is False


def test_check_authorization_master_success(control_panel):
    """Test check authorization for master user."""
    control_panel.login_manager.login_panel("master", "1234")

    assert control_panel._check_authorization("master") is True


def test_check_authorization_master_fail(control_panel):
    """Test check authorization fails and shows error message."""
    result = control_panel._check_authorization("master")

    assert result is False
    assert "Unauthorized" in control_panel.ui.short_message1
    assert "master" in control_panel.ui.short_message2.lower()


def test_check_authorization_any_with_master(control_panel):
    """Test check authorization 'any' with master login."""
    control_panel.login_manager.login_panel("master", "1234")

    assert control_panel._check_authorization("any") is True


def test_check_authorization_any_with_guest(control_panel):
    """Test check authorization 'any' with guest login."""
    control_panel.login_manager.login_panel("guest", None)

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
# Zone Arm/Disarm Tests
# ============================================================================


def test_zone_arm_disarm_operations(control_panel):
    """Test zone arm/disarm operations through configuration manager."""
    # Zone operations are tested via configuration_manager
    # This is an integration point test
    zones = control_panel.configuration_manager.safety_zones

    assert isinstance(zones, dict)


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

    with patch.object(control_panel, "after"):
        result = control_panel.input_handler._handle_panel_login()

    assert result is True
    assert control_panel.login_manager.is_logged_in_panel is True
    assert control_panel.input_handler.digit_input == []


def test_handle_panel_login_fail_wrong_password(control_panel):
    """Test failed panel login with wrong password."""
    control_panel.input_handler.panel_id_input = "master"
    control_panel.input_handler.digit_input = [0, 0, 0, 0]

    result = control_panel.input_handler._handle_panel_login()

    assert result is False
    assert control_panel.login_manager.is_logged_in_panel is False
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

    # Try wrong password 3 times
    for _ in range(3):
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
