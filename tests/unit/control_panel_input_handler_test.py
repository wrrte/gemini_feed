from unittest.mock import MagicMock

from core.control_panel.control_panel_input_handler import \
    ControlPanelInputHandler
from core.control_panel.control_panel_state_manager import ControlPanelState

# State constants
OFFLINE = ControlPanelState.OFFLINE
INIT = ControlPanelState.INITIALIZED
FUNC = ControlPanelState.FUNCTION_MODE
ALARM = ControlPanelState.RINGING_ALARM
PW_IN1 = ControlPanelState.MASTER_PASSWORD_CHANGE_INPUT_1
PW_IN2 = ControlPanelState.MASTER_PASSWORD_CHANGE_INPUT_2
DIGIT = ControlPanelState.DIGIT_INPUT
ID_IN = ControlPanelState.PANEL_ID_INPUT
LOCK = ControlPanelState.LOCKED


def make_handler():
    """Create handler with all mocked dependencies."""
    p = MagicMock()
    p.login_manager = MagicMock()
    p.login_manager.login_panel = MagicMock()
    p.login_manager.is_login_trials_exceeded = MagicMock(
        return_value=False
    )
    p.login_manager.login_trials = 0
    p.configuration_manager = MagicMock()
    p.ui = MagicMock()
    p._panic_button_press = MagicMock()
    p._turn_panel_on = MagicMock()
    p._turn_panel_off = MagicMock()
    p._reset_panel = MagicMock()
    p._navigate_to_previous_zone = MagicMock()
    p._navigate_to_next_zone = MagicMock()
    p._verify_login = MagicMock(return_value=False)
    p.after = MagicMock()
    p.after_cancel = MagicMock()
    p.alarm_manager = MagicMock()
    p._check_authorization = MagicMock(return_value=False)

    # Mock state_manager with side effect to update panel_state
    p.state_manager = MagicMock()
    p.state_manager.panel_state = OFFLINE
    p.state_manager._get_login_prefix = MagicMock(return_value="")

    # Configure change_state_to to actually update panel_state
    def change_state_side_effect(new_state, **kwargs):
        p.state_manager.panel_state = new_state

    p.state_manager.change_state_to = MagicMock(
        side_effect=change_state_side_effect
    )
    p.state_manager.start_lock_timer = MagicMock()
    p.state_manager.stop_alarm_ring = MagicMock()

    handler = ControlPanelInputHandler(parent=p)
    return handler


# A. handle_button_press()

def test_locked_state_blocks_input():
    """Button press blocked when locked."""
    h = make_handler()
    h.parent.state_manager.panel_state = LOCK
    h.handle_button_press("1")
    h.parent._turn_panel_on.assert_not_called()


def test_offline_button_1_turns_on():
    """Button 1 turns on panel from offline."""
    h = make_handler()
    h.parent.state_manager.panel_state = OFFLINE
    h.handle_button_press("1")
    h.parent._turn_panel_on.assert_called_once()


def test_offline_other_buttons_ignored():
    """Other buttons ignored in offline state."""
    h = make_handler()
    h.parent.state_manager.panel_state = OFFLINE
    h.handle_button_press("2")
    h.parent._turn_panel_on.assert_not_called()


def test_hash_returns_to_init():
    """# button returns to initialized (except offline/id_input)."""
    h = make_handler()

    # From OFFLINE - ignored
    h.parent.state_manager.panel_state = OFFLINE
    h.handle_button_press("#")
    h.parent.state_manager.change_state_to.assert_not_called()

    # From ID_INPUT - ignored
    h.parent.state_manager.panel_state = ID_IN
    h.parent.state_manager.change_state_to.reset_mock()
    h.handle_button_press("#")
    h.parent.state_manager.change_state_to.assert_not_called()

    # From INIT - returns to INIT
    h.parent.state_manager.panel_state = INIT
    h.parent.state_manager.change_state_to.reset_mock()
    h.handle_button_press("#")
    h.parent.state_manager.change_state_to.assert_called_with(INIT)


def test_hash_stops_alarm():
    """# button stops alarm and returns to init."""
    h = make_handler()
    h.parent.state_manager.panel_state = ALARM
    h.handle_button_press("#")
    h.parent.state_manager.stop_alarm_ring()
    h.parent.state_manager.change_state_to(INIT)


def test_panic_button_behavior():
    """Panic button ignored offline, triggers otherwise."""
    h = make_handler()

    # Offline - ignored
    h.parent.state_manager.panel_state = OFFLINE
    h.handle_button_press("panic")
    h.parent._panic_button_press.assert_not_called()

    # Not offline - triggers
    h.parent.state_manager.panel_state = INIT
    h.parent._panic_button_press.reset_mock()
    h.handle_button_press("panic")
    h.parent._panic_button_press.assert_called_once()


def test_init_state_button_6_enters_function():
    """Button 6 enters function mode from init."""
    h = make_handler()
    h.parent.state_manager.panel_state = INIT
    h.handle_button_press("6")
    assert h.parent.state_manager.panel_state == FUNC


def test_init_state_other_buttons_ignored():
    """Other buttons ignored in init state."""
    h = make_handler()
    h.parent.state_manager.panel_state = INIT
    h.handle_button_press("1")
    assert h.parent.state_manager.panel_state == INIT


def test_state_specific_handlers_called():
    """Correct handler called for each state."""
    h = make_handler()

    # Function mode
    h.parent.state_manager.panel_state = FUNC
    h._handle_function_mode_button_press = MagicMock()
    h.handle_button_press("1")
    h._handle_function_mode_button_press.assert_called_once_with("1")

    # Digit input
    h.parent.state_manager.panel_state = DIGIT
    h._handle_digit_input_button_press = MagicMock()
    h.handle_button_press("1")
    h._handle_digit_input_button_press.assert_called_once_with("1")

    # Panel ID input
    h.parent.state_manager.panel_state = ID_IN
    h._handle_panel_id_input_button_press = MagicMock()
    h.handle_button_press("*")
    h._handle_panel_id_input_button_press.assert_called_once_with("*")

    # Password change 1
    h.parent.state_manager.panel_state = PW_IN1
    h._handle_master_password_change_button_press = MagicMock()
    h.handle_button_press("1")
    h._handle_master_password_change_button_press.assert_called_with("1")

    # Password change 2
    h.parent.state_manager.panel_state = PW_IN2
    h._handle_master_password_change_button_press.reset_mock()
    h.handle_button_press("1")
    h._handle_master_password_change_button_press.assert_called_with("1")


# B. _handle_function_mode_button_press()

def test_function_buttons_1_2():
    """Function buttons 1/2 turn on/off."""
    h = make_handler()
    h._handle_function_mode_button_press("1")
    h.parent._turn_panel_on.assert_called_once()

    h._handle_function_mode_button_press("2")
    h.parent._turn_panel_off.assert_called_once()


def test_function_button_3_reset_auth():
    """Button 3 resets with master auth."""
    h = make_handler()

    # Without auth
    h._handle_function_mode_button_press("3")
    h.parent._reset_panel.assert_not_called()

    # With auth
    h.parent._check_authorization.return_value = True
    h._handle_function_mode_button_press("3")
    h.parent._reset_panel.assert_called_once()


def test_function_button_4_away_mode():
    """Button 4 changes to away mode with auth."""
    h = make_handler()

    # Without auth
    h._handle_function_mode_button_press("4")
    h.parent.configuration_manager.change_to_safehome_mode\
        .assert_not_called()

    # With auth - success
    h.parent._check_authorization.return_value = True
    h._handle_function_mode_button_press("4")
    h.parent.configuration_manager.change_to_safehome_mode\
        .assert_called_with("Away")
    h.parent.ui.set_display_away.assert_called_with(True)
    h.parent.ui.set_display_home.assert_called_with(False)

    # With auth - failure
    h.parent.configuration_manager.change_to_safehome_mode\
        .return_value = False
    h.parent.ui.set_display_messages.reset_mock()
    h._handle_function_mode_button_press("4")
    h.parent.ui.set_display_messages.assert_called_with(
        "Failed to change to away mode", "Please try again"
    )


def test_function_button_5_home_mode():
    """Button 5 changes to home mode with auth."""
    h = make_handler()

    # Without auth
    h._handle_function_mode_button_press("5")
    h.parent.configuration_manager.change_to_safehome_mode\
        .assert_not_called()

    # With auth - success
    h.parent._check_authorization.return_value = True
    h._handle_function_mode_button_press("5")
    h.parent.configuration_manager.change_to_safehome_mode\
        .assert_called_with("Home")
    h.parent.ui.set_display_away.assert_called_with(False)
    h.parent.ui.set_display_home.assert_called_with(True)

    # With auth - failure
    h.parent.configuration_manager.change_to_safehome_mode\
        .return_value = False
    h.parent.ui.set_display_messages.reset_mock()
    h._handle_function_mode_button_press("5")
    h.parent.ui.set_display_messages.assert_called_with(
        "Failed to change to home mode", "Please try again"
    )


def test_function_button_6_returns():
    """Button 6 does nothing (reserved)."""
    h = make_handler()
    h._handle_function_mode_button_press("6")
    h.parent._turn_panel_on.assert_not_called()


def test_function_button_7_9_navigate():
    """Buttons 7/9 navigate zones with auth."""
    h = make_handler()

    # Without auth
    h._handle_function_mode_button_press("7")
    h.parent._navigate_to_previous_zone.assert_not_called()
    h._handle_function_mode_button_press("9")
    h.parent._navigate_to_next_zone.assert_not_called()

    # With auth
    h.parent._check_authorization.return_value = True
    h._handle_function_mode_button_press("7")
    h.parent._navigate_to_previous_zone.assert_called_once()
    h._handle_function_mode_button_press("9")
    h.parent._navigate_to_next_zone.assert_called_once()


def test_function_button_8_toggle_arm():
    """Button 8 toggles zone arm state with auth."""
    h = make_handler()
    h._toggle_current_zone_arm_state = MagicMock()

    # Without auth
    h._handle_function_mode_button_press("8")
    h._toggle_current_zone_arm_state.assert_not_called()

    # With auth
    h.parent._check_authorization.return_value = True
    h._handle_function_mode_button_press("8")
    h._toggle_current_zone_arm_state.assert_called_once()


def test_function_button_0_password_change():
    """Button 0 starts password change with auth."""
    h = make_handler()

    # Without auth
    prev = h.parent.state_manager.panel_state
    h._handle_function_mode_button_press("0")
    assert h.parent.state_manager.panel_state == prev

    # With auth
    h.parent._check_authorization.return_value = True
    h._handle_function_mode_button_press("0")
    assert h.parent.state_manager.panel_state == PW_IN1


def test_function_button_star_hash():
    """Button * starts ID input, # does nothing."""
    h = make_handler()

    h._handle_function_mode_button_press("*")
    assert h.parent.state_manager.panel_state == ID_IN

    h.parent.state_manager.panel_state = FUNC
    h._handle_function_mode_button_press("#")
    assert h.parent.state_manager.panel_state == FUNC


# C. _handle_digit_input_button_press()

def test_digit_input_non_digit_ignored():
    """Non-digit buttons ignored in digit input."""
    h = make_handler()
    h._handle_digit_input_button_press("*")
    assert h.digit_input == []


def test_digit_input_appends_and_login():
    """Digits appended, login triggered at 4 digits."""
    h = make_handler()
    h._handle_panel_login = MagicMock()

    # Single digit
    h._handle_digit_input_button_press("1")
    assert h.digit_input == [1]
    h.parent.ui.set_display_messages.assert_called_once()

    # 4 digits trigger login
    for b in ["2", "3", "4"]:
        h._handle_digit_input_button_press(b)
    assert h.digit_input == [1, 2, 3, 4]
    h._handle_panel_login.assert_called()


# D. _handle_panel_id_input_button_press()

def test_id_input_star_selects_master():
    """* selects master and moves to digit input."""
    h = make_handler()
    h.digit_input = [1, 2, 3]
    h._handle_panel_id_input_button_press("*")
    assert h.panel_id_input == "master"
    assert h.digit_input == []
    assert h.parent.state_manager.panel_state == DIGIT


def test_id_input_hash_selects_guest():
    """# selects guest, tries login, moves to digit if fail."""
    h = make_handler()
    h._handle_panel_login = MagicMock(return_value=False)

    h._handle_panel_id_input_button_press("#")
    assert h.panel_id_input == "guest"
    h._handle_panel_login.assert_called_once()
    assert h.parent.state_manager.panel_state == DIGIT

    # Success - no state change
    h._handle_panel_login.return_value = True
    h.parent.state_manager.change_state_to.reset_mock()
    h._handle_panel_id_input_button_press("#")
    h.parent.state_manager.change_state_to.assert_not_called()


def test_id_input_other_ignored():
    """Other buttons ignored in ID input."""
    h = make_handler()
    h._handle_panel_id_input_button_press("1")
    assert h.panel_id_input == ""
    assert h.digit_input == []


# E. _handle_master_password_change_button_press()

def test_pw_change_non_digit_ignored():
    """Non-digit ignored in password change."""
    h = make_handler()
    h.parent.state_manager.panel_state = PW_IN1
    h._handle_master_password_change_button_press("*")
    assert h.digit_input == []


def test_pw_change_input_1_collects():
    """First password input collected and masked."""
    h = make_handler()
    h.parent.state_manager.panel_state = PW_IN1

    # 1 digit
    h._handle_master_password_change_button_press("1")
    assert h.digit_input == [1]
    h.parent.ui.set_display_short_message2.assert_called_with(
        "New password: *"
    )

    # 3 digits
    for b in ["2", "3"]:
        h._handle_master_password_change_button_press(b)
    h.parent.ui.set_display_short_message2.assert_called_with(
        "New password: ***"
    )

    # 4 digits - transition
    h._handle_master_password_change_button_press("4")
    assert h.new_password_temp == "1234"
    assert h.digit_input == []
    assert h.parent.state_manager.panel_state == PW_IN2


def test_pw_change_input_2_match():
    """Second password matched shows success."""
    h = make_handler()
    h.parent.state_manager.panel_state = PW_IN2
    h.new_password_temp = "1234"

    # 2 digits masked
    for b in ["1", "2"]:
        h._handle_master_password_change_button_press(b)
    h.parent.ui.set_display_short_message2.assert_called_with(
        "Confirm: **"
    )

    # 4 digits match
    for b in ["3", "4"]:
        h._handle_master_password_change_button_press(b)
    h.parent.ui.set_display_messages.assert_any_call(
        "Password changed!",
        "Successfully updated",
        h.parent.state_manager._get_login_prefix()
    )
    assert h.digit_input == []
    assert h.new_password_temp == ""


def test_pw_change_input_2_mismatch():
    """Second password mismatch shows error."""
    h = make_handler()
    h.parent.state_manager.panel_state = PW_IN2
    h.new_password_temp = "1234"

    for b in ["9", "9", "9", "9"]:
        h._handle_master_password_change_button_press(b)

    h.parent.ui.set_display_messages.assert_any_call(
        "Password mismatch!",
        "Please try again",
        h.parent.state_manager._get_login_prefix()
    )
    assert h.digit_input == []
    assert h.new_password_temp == ""
    h.parent.after.assert_called()


# F. _handle_panel_login()

def test_login_validation():
    """Login validates digit count and type."""
    h = make_handler()
    h.panel_id_input = "master"

    # Insufficient digits
    h.digit_input = [1, 2]
    assert h._handle_panel_login() is False

    # Non-int input
    h.digit_input = [1, "x", 3, 4]
    result = h._handle_panel_login()
    assert result is False
    assert h.digit_input == []
    h.parent.ui.set_display_short_message1.assert_called_with(
        "Invalid input", h.parent.state_manager._get_login_prefix()
    )


def test_login_guest_no_password():
    """Guest login allowed without password."""
    h = make_handler()
    h.panel_id_input = "guest"
    h.digit_input = []
    h.parent.login_manager.login_panel.return_value = True
    assert h._handle_panel_login() is True


def test_login_success():
    """Successful login clears input and shows message."""
    h = make_handler()
    h.panel_id_input = "master"
    h.digit_input = [1, 2, 3, 4]
    h.parent.login_manager.login_panel.return_value = True

    result = h._handle_panel_login()
    assert result is True
    h.parent.login_manager.login_panel.assert_called_with(
        "master", "1234"
    )
    assert h.digit_input == []
    h.parent.ui.set_display_short_message1.assert_called_once()
    h.parent.after.assert_called()


def test_login_failure():
    """Failed login shows retry message or locks."""
    h = make_handler()
    h.panel_id_input = "master"
    h.digit_input = [1, 2, 3, 4]
    h.parent.login_manager.login_panel.return_value = False
    h.parent.login_manager.login_trials = 1

    # Normal failure
    result = h._handle_panel_login()
    assert result is False
    h.parent.ui.set_display_short_message1.assert_called_once()
    assert h.digit_input == []

    # Max trials exceeded
    h.parent.login_manager.is_login_trials_exceeded.return_value = True
    h.digit_input = [0, 0, 0, 0]
    h._handle_panel_login()
    h.parent.state_manager.start_lock_timer.assert_called()


# G. _toggle_current_zone_arm_state()

def test_toggle_arm_validation():
    """Toggle validates zone selection."""
    h = make_handler()

    # No zone selected
    h.parent.ui.security_zone_number = None
    h._toggle_current_zone_arm_state()
    h.parent.configuration_manager.arm_safety_zone.assert_not_called()

    # Zone not found
    h.parent.ui.security_zone_number = 999
    h.parent.configuration_manager.safety_zones = {}
    h._toggle_current_zone_arm_state()
    h.parent.configuration_manager.arm_safety_zone.assert_not_called()


def test_toggle_arm_disarm_operations():
    """Toggle arms/disarms based on current state."""
    h = make_handler()
    h.parent.ui.security_zone_number = 1
    zone = MagicMock()
    h.parent.configuration_manager.safety_zones = {1: zone}

    # Disarm when armed
    zone.is_armed.return_value = True
    h.parent.configuration_manager.disarm_safety_zone.return_value = True
    h._toggle_current_zone_arm_state()
    h.parent.configuration_manager.disarm_safety_zone\
        .assert_called_with(1)
    h.parent.ui.set_armed_led.assert_called_with(True)

    # Arm when disarmed
    zone.is_armed.return_value = False
    h.parent.configuration_manager.arm_safety_zone.return_value = True
    h.parent.ui.set_armed_led.reset_mock()
    h._toggle_current_zone_arm_state()
    h.parent.configuration_manager.arm_safety_zone.assert_called_with(1)
    h.parent.ui.set_armed_led.assert_called_with(False)

    # Failure
    h.parent.configuration_manager.arm_safety_zone.return_value = False
    h._toggle_current_zone_arm_state()
    h.parent.ui.set_display_messages.assert_called_with(
        "Failed to arm/disarm zone", "Please try again"
    )
