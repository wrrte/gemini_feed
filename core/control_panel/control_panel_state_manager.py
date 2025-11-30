"""
Control Panel State Manager.

This module handles all state management functionality for the control panel,
including state transitions and timer management.
"""

import time
from enum import Enum
from typing import TYPE_CHECKING, Optional

# isort: off
from constants import (
    PANEL_LOCK_TIME_SECONDS,
    PANEL_DEFAULT_MESSAGE1,
    PANEL_DEFAULT_MESSAGE2,
    FUNCTION_MODE_MESSAGE1,
    FUNCTION_MODE_MESSAGE2,
)

# isort: on

if TYPE_CHECKING:
    from core.control_panel.control_panel import ControlPanel


class ControlPanelState(Enum):
    """Enum representing different states of the control panel."""

    INITIALIZED = "initialized"
    OFFLINE = "offline"
    PANEL_ID_INPUT = "panel_id_input"
    DIGIT_INPUT = "digit_input"
    LOCKED = "locked"
    FUNCTION_MODE = "function_mode"
    PANIC_MODE = "panic_mode"
    MASTER_PASSWORD_CHANGE_INPUT_1 = "master_password_change_input_1"
    MASTER_PASSWORD_CHANGE_INPUT_2 = "master_password_change_input_2"
    RINGING_ALARM = "ringing_alarm"


class ControlPanelStateManager:
    """Manages state transitions and timers for the control panel."""

    def __init__(self, parent: "ControlPanel"):
        """
        Initialize the state manager.

        Args:
            parent: Parent ControlPanel instance
        """
        self.parent = parent
        self.panel_state = ControlPanelState.OFFLINE
        self.lock_start_time = None
        self.lock_duration_sec = PANEL_LOCK_TIME_SECONDS
        self.lock_timer_id = None
        self.ring_start_time = None
        self.ring_duration_sec = 30
        self.ring_timer_id = None

    def get_state(self) -> ControlPanelState:
        """Get current panel state."""
        return self.panel_state

    def change_state_to(
        self,
        new_state: ControlPanelState,
        custom_message1: Optional[str] = None,
        custom_message2: Optional[str] = None,
    ) -> None:
        """
        Change panel state with proper cleanup and initialization.

        Args:
            new_state: Target state to transition to
            custom_message1: Optional custom message for line 1
            custom_message2: Optional custom message for line 2
        """
        old_state = self.panel_state
        self.panel_state = new_state

        # Log state transition (useful for debugging)
        print(f"State transition: {old_state.value} -> {new_state.value}")

        # Get login prefix for messages
        login_prefix = self._get_login_prefix()

        # State-specific initialization
        if new_state == ControlPanelState.INITIALIZED:
            self.parent.input_handler.digit_input = []
            self.parent.input_handler.panel_id_input = ""
            self.parent.input_handler.new_password_temp = ""
            msg1 = custom_message1 or PANEL_DEFAULT_MESSAGE1
            msg2 = custom_message2 or PANEL_DEFAULT_MESSAGE2
            self.parent.ui.set_display_messages(msg1, msg2, login_prefix)

        elif new_state == ControlPanelState.OFFLINE:
            self.parent.powered = False
            self.parent.input_handler.panel_id_input = ""
            self.parent.input_handler.digit_input = []
            self.parent.ui.set_powered_led(False)
            self.parent.ui.set_armed_led(False)
            self.parent.ui.set_display_away(False)
            self.parent.ui.set_display_home(False)
            self.parent.ui.set_display_not_ready(False)
            self.parent.ui.set_display_messages("turn-off", "", "")

        elif new_state == ControlPanelState.FUNCTION_MODE:
            msg1 = custom_message1 or FUNCTION_MODE_MESSAGE1
            msg2 = custom_message2 or FUNCTION_MODE_MESSAGE2
            self.parent.ui.set_display_messages(msg1, msg2, login_prefix)

        elif new_state == ControlPanelState.PANEL_ID_INPUT:
            self.parent.input_handler.digit_input = []
            self.parent.input_handler.panel_id_input = ""
            msg1 = custom_message1 or "Enter panel ID."
            msg2 = custom_message2 or "* for MASTER, # for GUEST"
            self.parent.ui.set_display_messages(msg1, msg2, login_prefix)

        elif new_state == ControlPanelState.DIGIT_INPUT:
            # digit_input은 이미 초기화되어 있어야 함
            msg1 = custom_message1 or "Enter 4 digits password."
            msg2 = custom_message2 or ""
            self.parent.ui.set_display_messages(msg1, msg2, login_prefix)

        elif new_state == ControlPanelState.MASTER_PASSWORD_CHANGE_INPUT_1:
            self.parent.input_handler.digit_input = []
            self.parent.input_handler.new_password_temp = ""
            msg1 = custom_message1 or "Enter new password (4 digits)"
            msg2 = custom_message2 or ""
            self.parent.ui.set_display_messages(msg1, msg2, login_prefix)

        elif new_state == ControlPanelState.MASTER_PASSWORD_CHANGE_INPUT_2:
            self.parent.input_handler.digit_input = []
            # new_password_temp는 유지
            msg1 = custom_message1 or "Re-enter new password"
            msg2 = custom_message2 or ""
            self.parent.ui.set_display_messages(msg1, msg2, login_prefix)

        elif new_state == ControlPanelState.LOCKED:
            self.lock_start_time = time.time()
            self._update_lock_timer()

        elif new_state == ControlPanelState.PANIC_MODE:
            self.panel_state = ControlPanelState.PANIC_MODE

        elif new_state == ControlPanelState.RINGING_ALARM:
            self.ring_start_time = time.time()
            self._update_ring_timer()

    def _get_login_prefix(self) -> str:
        """Get login status prefix for display messages."""
        if self.parent.login_manager:
            if self.parent._verify_login("master"):
                return "(master) "
            elif self.parent._verify_login("guest"):
                return "(guest) "
            else:
                return "(unauthorized) "
        else:
            return "(system) "

    def start_lock_timer(self):
        """Start panel lock with timer."""
        self.change_state_to(ControlPanelState.LOCKED)

    def _update_lock_timer(self):
        """Update lock timer display every second."""
        if self.lock_start_time is None:
            return

        # calculate remaining time
        elapsed = time.time() - self.lock_start_time
        remaining = max(0, self.lock_duration_sec - elapsed)

        if remaining > 0:
            # display remaining time
            login_prefix = self._get_login_prefix()
            self.parent.ui.set_display_messages(
                "Panel is locked",
                f"Unlock in {int(remaining)}s",
                login_prefix,
            )

            # update again after 1 second
            self.lock_timer_id = self.parent.after(
                1000, self._update_lock_timer
            )
        else:
            # unlock panel
            self.unlock_panel()

    def unlock_panel(self):
        """Unlock panel and reset state."""
        self.cancel_all_timers()
        self.change_state_to(ControlPanelState.INITIALIZED)

    def start_ring_alarm_and_external_call(self):
        """
        Start ring alarm.
        If new intrusion is detected, cancel timer and restart ringing alarm
        and make an external call.
        """
        # if timer is running, cancel it
        if self.ring_timer_id:
            self.parent.after_cancel(self.ring_timer_id)
            self.ring_timer_id = None

        # start ringing alarm
        self.change_state_to(ControlPanelState.RINGING_ALARM)

    def _update_ring_timer(self):
        """Update ring timer display every second."""
        if self.ring_start_time is None:
            return

        elapsed = time.time() - self.ring_start_time
        remaining = max(0, self.ring_duration_sec - elapsed)

        if remaining > 0:
            login_prefix = self._get_login_prefix()
            self.parent.ui.set_display_messages(
                "Alarm ringing",
                f"External call starts in {int(remaining)}s",
                login_prefix,
            )

            # update again after 1 second
            self.ring_timer_id = self.parent.after(
                1000, self._update_ring_timer
            )
        else:
            # 타이머 종료
            self.ring_timer_id = None
            self.ring_start_time = None

            # start external call
            login_prefix = self._get_login_prefix()
            self.parent.ui.set_display_messages(
                "Alarm ringing...",
                "External call Started...",
                login_prefix,
            )
            self.parent._panic_button_press()

    def stop_alarm_ring(self):
        """Stop alarm ring and cancel timer."""
        # Cancel ring timer
        if self.ring_timer_id:
            self.parent.after_cancel(self.ring_timer_id)
            self.ring_timer_id = None
        self.ring_start_time = None

        # Stop alarm
        if self.parent.alarm_manager:
            self.parent.alarm_manager.stop_alarm()

    def cancel_all_timers(self):
        """Cancel all timers and reset their state."""
        # Lock 타이머 취소
        if self.lock_timer_id:
            self.parent.after_cancel(self.lock_timer_id)
            self.lock_timer_id = None
        self.lock_start_time = None

        # Ring 타이머 취소
        if self.ring_timer_id:
            self.parent.after_cancel(self.ring_timer_id)
            self.ring_timer_id = None
        self.ring_start_time = None
