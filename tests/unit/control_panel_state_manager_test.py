import time
from unittest.mock import MagicMock

from core.control_panel.control_panel_state_manager import (
    ControlPanelState, ControlPanelStateManager)

OFFLINE = ControlPanelState.OFFLINE
INITIALIZED = ControlPanelState.INITIALIZED
FUNCTION_MODE = ControlPanelState.FUNCTION_MODE
RINGING_ALARM = ControlPanelState.RINGING_ALARM
LOCKED = ControlPanelState.LOCKED

# Helper to make a manager with mocked dependencies


def make_manager():
    parent = MagicMock()
    # ui methods used by manager
    parent.ui = MagicMock()
    parent.ui.set_display_messages = MagicMock()
    parent.ui.set_powered_led = MagicMock()
    parent.ui.set_armed_led = MagicMock()
    parent.ui.set_display_away = MagicMock()
    parent.ui.set_display_home = MagicMock()
    parent.ui.set_display_not_ready = MagicMock()
    # timers: return dummy token; do NOT invoke callbacks automatically
    parent.after = MagicMock(return_value=object())
    parent.after_cancel = MagicMock()
    # alarm manager
    parent.alarm_manager = MagicMock()
    parent.alarm_manager.stop_alarm = MagicMock()
    # panel helpers
    parent._panic_button_press = MagicMock()
    parent._verify_login = MagicMock(return_value=False)
    parent.login_manager = MagicMock()
    # input handler fields expected to be present
    parent.input_handler = MagicMock()
    parent.input_handler.digit_input = []
    parent.input_handler.panel_id_input = ""
    parent.input_handler.new_password_temp = ""
    # powered flag
    parent.powered = True

    manager = ControlPanelStateManager(parent=parent)
    return manager


# get_state


def test_get_state_returns_current_state():
    mgr = make_manager()
    assert mgr.get_state() == ControlPanelState.OFFLINE
    mgr.panel_state = ControlPanelState.INITIALIZED
    assert mgr.get_state() == ControlPanelState.INITIALIZED


# change_state_to -> INITIALIZED


def test_change_state_to_initialized_resets_inputs_and_updates_ui():
    mgr = make_manager()
    mgr.parent.input_handler.digit_input = [1, 2]
    mgr.parent.input_handler.panel_id_input = "master"
    mgr.parent.input_handler.new_password_temp = "1234"
    mgr.change_state_to(ControlPanelState.INITIALIZED)
    assert mgr.panel_state == ControlPanelState.INITIALIZED
    assert mgr.parent.input_handler.digit_input == []
    assert mgr.parent.input_handler.panel_id_input == ""
    assert mgr.parent.input_handler.new_password_temp == ""
    mgr.parent.ui.set_display_messages.assert_called()


# change_state_to -> OFFLINE


def test_change_state_to_offline_updates_leds_and_ui_and_resets_inputs():
    mgr = make_manager()
    mgr.change_state_to(ControlPanelState.OFFLINE)
    assert mgr.panel_state == ControlPanelState.OFFLINE
    mgr.parent.ui.set_powered_led.assert_called_with(False)
    mgr.parent.ui.set_armed_led.assert_called_with(False)
    mgr.parent.ui.set_display_away.assert_called_with(False)
    mgr.parent.ui.set_display_home.assert_called_with(False)
    mgr.parent.ui.set_display_not_ready.assert_called_with(False)
    mgr.parent.ui.set_display_messages.assert_called_with("turn-off", "", "")


# change_state_to -> FUNCTION_MODE


def test_change_state_to_function_mode_sets_function_messages():
    mgr = make_manager()
    mgr.change_state_to(ControlPanelState.FUNCTION_MODE)
    assert mgr.panel_state == ControlPanelState.FUNCTION_MODE
    mgr.parent.ui.set_display_messages.assert_called()


# change_state_to -> PANEL_ID_INPUT


def test_change_state_to_panel_id_input_resets_inputs_and_prompts():
    mgr = make_manager()
    mgr.change_state_to(ControlPanelState.PANEL_ID_INPUT)
    assert mgr.panel_state == ControlPanelState.PANEL_ID_INPUT
    assert mgr.parent.input_handler.digit_input == []
    assert mgr.parent.input_handler.panel_id_input == ""
    mgr.parent.ui.set_display_messages.assert_called()


# change_state_to -> DIGIT_INPUT


def test_change_state_to_digit_input_prompts_for_password():
    mgr = make_manager()
    mgr.change_state_to(ControlPanelState.DIGIT_INPUT)
    assert mgr.panel_state == ControlPanelState.DIGIT_INPUT
    mgr.parent.ui.set_display_messages.assert_called()


# change_state_to -> MASTER_PASSWORD_CHANGE_INPUT_1


def test_change_state_to_master_password_change_input_1():
    mgr = make_manager()
    mgr.parent.input_handler.new_password_temp = "x"
    mgr.parent.input_handler.digit_input = [1]
    mgr.change_state_to(ControlPanelState.MASTER_PASSWORD_CHANGE_INPUT_1)
    assert mgr.panel_state == ControlPanelState.MASTER_PASSWORD_CHANGE_INPUT_1
    assert mgr.parent.input_handler.digit_input == []
    assert mgr.parent.input_handler.new_password_temp == ""
    mgr.parent.ui.set_display_messages.assert_called()


# change_state_to -> MASTER_PASSWORD_CHANGE_INPUT_2


def test_change_state_to_master_password_change_input_2():
    mgr = make_manager()
    mgr.parent.input_handler.new_password_temp = "1234"
    mgr.change_state_to(ControlPanelState.MASTER_PASSWORD_CHANGE_INPUT_2)
    assert mgr.panel_state == ControlPanelState.MASTER_PASSWORD_CHANGE_INPUT_2
    assert mgr.parent.input_handler.digit_input == []
    assert mgr.parent.input_handler.new_password_temp == "1234"
    mgr.parent.ui.set_display_messages.assert_called()


# change_state_to -> LOCKED


def test_change_state_to_locked_starts_lock_timer():
    mgr = make_manager()
    mgr.change_state_to(ControlPanelState.LOCKED)
    assert mgr.panel_state == ControlPanelState.LOCKED
    assert mgr.lock_start_time is not None


# change_state_to -> PANIC_MODE


def test_change_state_to_panic_mode_sets_state():
    mgr = make_manager()
    mgr.change_state_to(ControlPanelState.PANIC_MODE)
    assert mgr.panel_state == ControlPanelState.PANIC_MODE


# change_state_to -> RINGING_ALARM


def test_change_state_to_ringing_alarm_starts_ring_timer():
    mgr = make_manager()
    mgr.change_state_to(ControlPanelState.RINGING_ALARM)
    assert mgr.panel_state == ControlPanelState.RINGING_ALARM
    assert mgr.ring_start_time is not None


# _get_login_prefix


def test_get_login_prefix_master_guest_unauthorized():
    mgr = make_manager()
    mgr.parent._verify_login.side_effect = lambda role: role == "master"
    assert mgr._get_login_prefix() == "(master) "
    mgr.parent._verify_login.side_effect = lambda role: role == "guest"
    assert mgr._get_login_prefix() == "(guest) "
    mgr.parent._verify_login.side_effect = lambda role: False
    assert mgr._get_login_prefix() == "(unauthorized) "


# start_lock_timer


def test_start_lock_timer_sets_locked_state():
    mgr = make_manager()
    mgr.start_lock_timer()
    assert mgr.panel_state == ControlPanelState.LOCKED


# _update_lock_timer unlocks after duration


def test_update_lock_timer_unlocks_when_remaining_zero():
    mgr = make_manager()
    mgr.lock_duration_sec = 0
    mgr.change_state_to(ControlPanelState.LOCKED)
    # With zero duration, _update_lock_timer should unlock immediately
    assert mgr.panel_state == ControlPanelState.INITIALIZED


# unlock_panel cancels timers and go initialized


def test_unlock_panel_cancels_timers_and_goes_initialized():
    mgr = make_manager()
    mgr.lock_timer_id = object()
    mgr.ring_timer_id = object()
    mgr.lock_start_time = time.time()
    mgr.ring_start_time = time.time()
    mgr.unlock_panel()
    assert mgr.panel_state == ControlPanelState.INITIALIZED
    assert mgr.lock_timer_id is None
    assert mgr.ring_timer_id is None
    assert mgr.lock_start_time is None
    assert mgr.ring_start_time is None


# start_count_down_for_external_call sets RINGING_ALARM and schedules timer


def test_start_count_down_for_external_call_sets_ringing_alarm_and_schedules():
    mgr = make_manager()
    mgr.start_count_down_for_external_call()
    assert mgr.panel_state == ControlPanelState.RINGING_ALARM
    assert mgr.ring_start_time is not None


# _update_ring_timer finishes and triggers external call


def test_update_ring_timer_calls_external_when_time_elapsed():
    mgr = make_manager()
    mgr.ring_duration_sec = 0
    mgr.start_count_down_for_external_call()
    # Manually invoke the update to simulate timer tick
    mgr._update_ring_timer()
    mgr.parent._panic_button_press.assert_called()


# stop_alarm_ring cancels timers and stops alarm


def test_stop_alarm_ring_cancels_timer_and_stops_alarm():
    mgr = make_manager()
    token = object()
    mgr.ring_timer_id = token
    mgr.ring_start_time = time.time()
    mgr.stop_alarm_ring()
    assert mgr.ring_timer_id is None
    assert mgr.ring_start_time is None
    mgr.parent.after_cancel.assert_called_with(token)
    mgr.parent.alarm_manager.stop_alarm.assert_called()


# cancel_all_timers cancels both and resets


def test_cancel_all_timers_cancels_and_resets_all():
    mgr = make_manager()
    lock_token = object()
    ring_token = object()
    mgr.lock_timer_id = lock_token
    mgr.ring_timer_id = ring_token
    mgr.lock_start_time = time.time()
    mgr.ring_start_time = time.time()
    mgr.cancel_all_timers()
    mgr.parent.after_cancel.assert_any_call(lock_token)
    mgr.parent.after_cancel.assert_any_call(ring_token)
    assert mgr.lock_timer_id is None
    assert mgr.ring_timer_id is None
    assert mgr.lock_start_time is None
    assert mgr.ring_start_time is None


# _get_login_prefix returns "(system) " when login_manager is None
def test_get_login_prefix_no_login_manager():
    mgr = make_manager()
    mgr.parent.login_manager = None
    assert mgr._get_login_prefix() == "(system) "


# _update_lock_timer returns early when lock_start_time is None
def test_update_lock_timer_returns_when_lock_start_time_none():
    mgr = make_manager()
    mgr.lock_start_time = None
    # Should return early without calling any UI methods
    mgr._update_lock_timer()


# start_count_down_for_external_call cancels existing timer
def test_start_count_down_cancels_existing_ring_timer():
    mgr = make_manager()
    existing_timer_id = object()
    mgr.ring_timer_id = existing_timer_id
    mgr.start_count_down_for_external_call()
    # Should have cancelled the existing timer
    mgr.parent.after_cancel.assert_called_with(existing_timer_id)
    # And started new ringing alarm state
    assert mgr.panel_state == ControlPanelState.RINGING_ALARM
