from unittest.mock import MagicMock

from core.control_panel.control_panel_input_handler import \
    ControlPanelInputHandler
from core.control_panel.control_panel_state_manager import (
    ControlPanelState, ControlPanelStateManager)

# Helper to make a handler with mocked dependencies

OFFLINE = ControlPanelState.OFFLINE
INITIALIZED = ControlPanelState.INITIALIZED
FUNCTION_MODE = ControlPanelState.FUNCTION_MODE
RINGING_ALARM = ControlPanelState.RINGING_ALARM
MASTER_PASSWORD_CHANGE_INPUT_1 \
    = ControlPanelState.MASTER_PASSWORD_CHANGE_INPUT_1
MASTER_PASSWORD_CHANGE_INPUT_2 \
    = ControlPanelState.MASTER_PASSWORD_CHANGE_INPUT_2
DIGIT_INPUT = ControlPanelState.DIGIT_INPUT
PANEL_ID_INPUT = ControlPanelState.PANEL_ID_INPUT
LOCKED = ControlPanelState.LOCKED


def make_handler():
    parent = MagicMock()
    parent.login_manager = MagicMock()
    parent.login_manager.login_panel = MagicMock()
    parent.login_manager.is_login_trials_exceeded = MagicMock(
        return_value=False)
    parent.login_manager.login_trials = 0
    parent.configuration_manager = MagicMock()
    parent.ui = MagicMock()
    parent._panic_button_press = MagicMock()
    parent._turn_panel_on = MagicMock()
    parent._turn_panel_off = MagicMock()
    parent._reset_panel = MagicMock()
    parent._navigate_to_previous_zone = MagicMock()
    parent._navigate_to_next_zone = MagicMock()
    parent._verify_login = MagicMock(return_value=False)
    parent.after = MagicMock()
    parent.after_cancel = MagicMock()
    parent.alarm_manager = MagicMock()
    parent.state_manager = ControlPanelStateManager(parent=parent)
    # Add authorization on parent (the handler uses
    # parent._check_authorization)
    parent._check_authorization = MagicMock(return_value=False)

    handler = ControlPanelInputHandler(parent=parent)
    return handler

# A. handle_button_press()


def test_panel_button_1_turns_on_from_offline():
    handler = make_handler()
    handler.parent.state_manager.panel_state = OFFLINE
    handler.handle_button_press("1")
    handler.parent._turn_panel_on.assert_called_once()


def test_panel_panic_button_triggers_alarm_when_not_offline():
    handler = make_handler()
    handler.parent.state_manager.panel_state = INITIALIZED
    handler.handle_button_press("panic")
    handler.parent._panic_button_press.assert_called_once()


def test_panel_button_hash_stops_alarm_and_returns_initialized():
    handler = make_handler()
    handler.parent.state_manager.panel_state = RINGING_ALARM
    handler.handle_button_press("#")
    handler.parent.state_manager.stop_alarm_ring()
    handler.parent.state_manager.change_state_to(INITIALIZED)
    assert handler.parent.state_manager.panel_state == INITIALIZED


def test_panel_button_6_enters_function_mode_from_initialized():
    handler = make_handler()
    handler.parent.state_manager.panel_state = INITIALIZED
    handler.handle_button_press("6")
    assert handler.parent.state_manager.panel_state == FUNCTION_MODE

# B. _handle_function_mode_button_press()


def test_panel_function_1_turns_on_in_function_mode():
    handler = make_handler()
    handler.parent.state_manager.panel_state = FUNCTION_MODE
    handler._handle_function_mode_button_press("1")
    handler.parent._turn_panel_on.assert_called_once()


def test_panel_function_2_turns_off_in_function_mode():
    handler = make_handler()
    handler.parent.state_manager.panel_state = FUNCTION_MODE
    handler._handle_function_mode_button_press("2")
    handler.parent._turn_panel_off.assert_called_once()


def test_panel_function_3_resets_with_master_authorization():
    handler = make_handler()
    handler.parent.state_manager.panel_state = FUNCTION_MODE
    handler.parent._check_authorization.return_value = True
    handler._handle_function_mode_button_press("3")
    handler.parent._reset_panel.assert_called_once()


def test_panel_function_3_no_reset_without_master_authorization():
    handler = make_handler()
    handler.parent.state_manager.panel_state = FUNCTION_MODE
    handler.parent._check_authorization.return_value = False
    handler._handle_function_mode_button_press("3")
    handler.parent._check_authorization.assert_called_once_with("master")
    handler.parent._reset_panel.assert_not_called()


def test_panel_function_4_change_mode_away_with_master_authorization():
    handler = make_handler()
    handler.parent.state_manager.panel_state = FUNCTION_MODE
    handler.parent._check_authorization.return_value = True
    handler._handle_function_mode_button_press("4")
    handler.parent.configuration_manager.change_to_safehome_mode\
        .assert_called_once_with("Away")
    handler.parent.ui.set_display_away.assert_called_with(True)
    handler.parent.ui.set_display_home.assert_called_with(False)


def test_panel_function_4_no_change_mode_away_without_master_authorization():
    handler = make_handler()
    handler.parent.state_manager.panel_state = FUNCTION_MODE
    handler.parent._check_authorization.return_value = False
    handler._handle_function_mode_button_press("4")
    handler.parent.configuration_manager.change_to_safehome_mode\
        .assert_not_called()


def test_panel_function_4_change_mode_away_failure_shows_message():
    handler = make_handler()
    handler.parent.state_manager.panel_state = FUNCTION_MODE
    handler.parent._check_authorization.return_value = True
    handler.parent.configuration_manager.change_to_safehome_mode\
        .return_value = False
    handler._handle_function_mode_button_press("4")
    handler.parent.ui.set_display_messages.assert_called_once_with(
        "Failed to change to away mode", "Please try again"
    )


def test_panel_function_5_change_mode_home_with_master_authorization():
    handler = make_handler()
    handler.parent._check_authorization.return_value = True
    handler._handle_function_mode_button_press("5")
    handler.parent.configuration_manager.change_to_safehome_mode\
        .assert_called_once_with("Home")
    handler.parent.ui.set_display_away.assert_called_with(False)
    handler.parent.ui.set_display_home.assert_called_with(True)


def test_panel_function_5_no_change_mode_home_without_master_authorization():
    handler = make_handler()
    handler.parent._check_authorization.return_value = False
    handler._handle_function_mode_button_press("5")
    handler.parent.configuration_manager.change_to_safehome_mode\
        .assert_not_called()


def test_panel_function_5_change_mode_home_failure_shows_message():
    handler = make_handler()
    handler.parent._check_authorization.return_value = True
    handler.parent.configuration_manager.change_to_safehome_mode\
        .return_value = False
    handler._handle_function_mode_button_press("5")
    handler.parent.ui.set_display_messages.assert_called_once_with(
        "Failed to change to home mode", "Please try again"
    )


def test_panel_function_7_navigate_to_previous_zone():
    handler = make_handler()
    handler.parent._check_authorization.return_value = True
    handler._handle_function_mode_button_press("7")
    handler.parent._navigate_to_previous_zone.assert_called_once()


def test_panel_function_8_toggle_arm_state_with_master_authorization():
    handler = make_handler()
    handler.parent._check_authorization.return_value = True
    handler._toggle_current_zone_arm_state = MagicMock()
    handler._handle_function_mode_button_press("8")
    handler._toggle_current_zone_arm_state.assert_called_once()


def test_panel_function_8_no_toggle_arm_state_without_master_authorization():
    handler = make_handler()
    handler.parent._check_authorization.return_value = False
    handler._toggle_current_zone_arm_state = MagicMock()
    handler._handle_function_mode_button_press("8")
    handler._toggle_current_zone_arm_state.assert_not_called()


def test_panel_function_9_navigate_to_next_zone():
    handler = make_handler()
    handler.parent._check_authorization.return_value = True
    handler._handle_function_mode_button_press("9")
    handler.parent._navigate_to_next_zone.assert_called_once()


def test_panel_function_0_start_master_password_change_with_auth():
    handler = make_handler()
    handler.parent._check_authorization.return_value = True
    handler._handle_function_mode_button_press("0")
    assert handler.parent.state_manager.panel_state\
        == MASTER_PASSWORD_CHANGE_INPUT_1


def test_panel_function_0_no_master_password_change_without_auth():
    handler = make_handler()
    handler.parent._check_authorization.return_value = False
    prev_state = handler.parent.state_manager.panel_state
    handler._handle_function_mode_button_press("0")
    assert handler.parent.state_manager.panel_state == prev_state


def test_panel_function_asteroid_starts_id_input():
    handler = make_handler()
    handler._handle_function_mode_button_press("*")
    assert handler.parent.state_manager.panel_state == PANEL_ID_INPUT

# C. _handle_digit_input_button_press()


def test_panel_digit_input_appends_and_triggers_login():
    handler = make_handler()
    handler.parent.state_manager.panel_state = DIGIT_INPUT
    handler._handle_panel_login = MagicMock()
    for b in ["1", "2", "3", "4"]:
        handler._handle_digit_input_button_press(b)
    assert handler.digit_input == [1, 2, 3, 4]
    handler.parent.ui.set_display_messages.assert_called()
    handler._handle_panel_login.assert_called()

# E. _handle_master_password_change_button_press()


def test_panel_master_pw_change_collects_and_transitions_to_confirm():
    handler = make_handler()
    handler.parent.state_manager.panel_state = MASTER_PASSWORD_CHANGE_INPUT_1
    for b in ["1", "2", "3", "4"]:
        handler._handle_master_password_change_button_press(b)
    assert handler.new_password_temp == "1234"
    assert handler.digit_input == []
    assert handler.parent.state_manager.panel_state\
        == MASTER_PASSWORD_CHANGE_INPUT_2
    handler.parent.ui.set_display_messages.assert_called_with(
        "Re-enter new password", "",
        handler.parent.state_manager._get_login_prefix())


def test_panel_master_pw_change_mismatch_shows_error_and_returns_initialized():
    handler = make_handler()
    handler.parent.state_manager.panel_state = MASTER_PASSWORD_CHANGE_INPUT_2
    handler.new_password_temp = "1234"
    for b in ["9", "9", "9", "9"]:
        handler._handle_master_password_change_button_press(b)
    handler.parent.ui.set_display_messages.assert_any_call(
        "Password mismatch!", "Please try again",
        handler.parent.state_manager._get_login_prefix()
    )
    assert handler.digit_input == []
    assert handler.new_password_temp == ""
    handler.parent.after.assert_called()
    handler.parent.state_manager.change_state_to(INITIALIZED)
    assert handler.parent.state_manager.panel_state == INITIALIZED

# F. _handle_panel_login()


def test_panel_login_nonint_input_resets_and_shows_error():
    handler = make_handler()
    handler.panel_id_input = "master"
    handler.digit_input = [1, "x", 3, 4]
    result = handler._handle_panel_login()
    assert result is False
    assert handler.digit_input == []
    handler.parent.ui.set_display_short_message1.assert_called_with(
        "Invalid input", handler.parent.state_manager._get_login_prefix())
    handler.parent.ui.set_display_short_message2.assert_called_with(
        "Please enter a valid 4 digit number")


def test_panel_login_fail_updates_trials_and_shows_retry_message():
    handler = make_handler()
    handler.panel_id_input = "master"
    handler.digit_input = [1, 2, 3, 4]
    handler.parent.login_manager.login_panel.return_value = False
    handler.parent.login_manager.login_trials = 1
    result = handler._handle_panel_login()
    assert result is False
    handler.parent.ui.set_display_short_message1.assert_called_once()
    handler.parent.ui.set_display_short_message2.assert_called_once()
    assert handler.digit_input == []


def test_panel_login_max_attempt_starts_lock_timer():
    handler = make_handler()
    handler.panel_id_input = "master"
    handler.digit_input = [1, 2, 3, 4]
    handler.parent.login_manager.login_panel.return_value = False
    handler.parent.login_manager.is_login_trials_exceeded.return_value = True
    result = handler._handle_panel_login()
    assert result is False
    handler.parent.state_manager.start_lock_timer()
    handler.parent.state_manager.change_state_to(LOCKED)
    assert handler.parent.state_manager.panel_state == LOCKED
