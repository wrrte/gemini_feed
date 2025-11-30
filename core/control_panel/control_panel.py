"""
Control Panel for SafeHome security system.

This is the main control panel window that coordinates UI, state management,
and input handling through composition.
"""

from typing import Callable, List, Literal, Optional

import customtkinter as ctk

from constants import UI_UPDATE_DELAY_MS
from core.control_panel.control_panel_input_handler import \
    ControlPanelInputHandler
from core.control_panel.control_panel_state_manager import (
    ControlPanelState, ControlPanelStateManager)
from core.control_panel.control_panel_ui import ControlPanelUI
from manager.configuration_manager import ConfigurationManager
from manager.login_manager import LoginManager


class ControlPanel(ctk.CTk):
    """
    Control Panel window for SafeHome security system.

    This class coordinates UI, state management, and input handling through
    composition. It maintains system-level operations like power control,
    authentication, and zone navigation.

    Note: A root window must exist before creating a Toplevel.
    """

    def __init__(
        self,
        turn_system_on: Callable[[], bool],
        turn_system_off: Callable[[], bool],
        set_reset_database: Callable[[bool], None],
        external_call: Callable[[], List[str]],
        login_manager: Optional[LoginManager],
        configuration_manager: Optional[ConfigurationManager],
        title: str = "Control Panel",
        width: int = 505,
        height: int = 300,
    ):
        """
        Initialize the Control Panel.

        Args:
            turn_system_on: Callback to turn system on
            turn_system_off: Callback to turn system off
            set_reset_database: Callback to set reset database flag
            external_call: Callback to make external emergency calls
            login_manager: Manager for login operations
            configuration_manager: Manager for system configuration
            title: Window title
            width: Window width in pixels
            height: Window height in pixels
        """
        super().__init__()
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)

        # Set callbacks
        self.turn_system_on = turn_system_on
        self.turn_system_off = turn_system_off
        self.set_reset_database = set_reset_database
        self.external_call = external_call

        # Initialize managers
        self.login_manager = login_manager
        self.configuration_manager = configuration_manager
        self.alarm_manager = None
        self.sensor_manager = None

        # Initialize state
        self.powered = False

        # Create components using composition
        self.ui = ControlPanelUI(self, width, height)
        self.state_manager = ControlPanelStateManager(self)
        self.input_handler = ControlPanelInputHandler(self)

        # Draw the control panel UI
        self.ui.draw_page(self.input_handler.handle_button_press)

    def set_managers(
        self,
        login_manager: LoginManager,
        configuration_manager: ConfigurationManager,
        alarm_manager=None,
        sensor_manager=None,
    ):
        """
        Set the managers.

        Args:
            login_manager: Manager for login operations
            configuration_manager: Manager for system configuration
            alarm_manager: Manager for alarm operations
            sensor_manager: Manager for sensor operations
        """
        self.login_manager = login_manager
        self.configuration_manager = configuration_manager
        self.alarm_manager = alarm_manager
        self.sensor_manager = sensor_manager

    def start_count_down_for_external_call(self):
        """
        Start count down for external call.
        """
        self.state_manager.start_count_down_for_external_call()

    def _turn_panel_on(self):
        """Turn panel on."""
        # if already powered, return
        if self.powered:
            return

        # Display message
        self.ui.set_display_not_ready(True)
        login_prefix = self.state_manager._get_login_prefix()
        self.after(
            UI_UPDATE_DELAY_MS,
            lambda: self.ui.set_display_short_message1(
                "Starting system...", login_prefix
            ),
        )
        self.ui.set_display_short_message2("Please wait...")

        # Turn system on
        try:
            if not self.turn_system_on():
                login_prefix = self.state_manager._get_login_prefix()
                self.ui.set_display_messages(
                    "System startup failed", "Please try again", login_prefix
                )
                return
        except Exception as e:
            login_prefix = self.state_manager._get_login_prefix()
            self.ui.set_display_messages(
                "System startup failed", f"Error: {e}", login_prefix
            )
            self.ui.set_display_not_ready(True)
            return

        # Powering up
        self.powered = True
        login_prefix = self.state_manager._get_login_prefix()
        self.after(
            UI_UPDATE_DELAY_MS,
            lambda: self.ui.set_display_short_message1(
                "Powering up...", login_prefix
            ),
        )
        self.after(UI_UPDATE_DELAY_MS, lambda: self.ui.set_powered_led(True))

        # Display zone number (minimum zone number)
        if self.ui.security_zone_number is None:
            zone_ids = sorted(self.configuration_manager.safety_zones.keys())
            if zone_ids:
                self.ui.set_security_zone_number(zone_ids[0])

        # Display zone arm status
        if self.ui.security_zone_number is not None:
            zone = self.configuration_manager.safety_zones.get(
                self.ui.security_zone_number
            )
            if zone:
                self.ui.set_armed_led(zone.is_armed())

        # System Ready
        self.after(
            UI_UPDATE_DELAY_MS,
            lambda: self.state_manager.change_state_to(
                ControlPanelState.INITIALIZED
            ),
        )
        self.after(
            UI_UPDATE_DELAY_MS, lambda: self.ui.set_display_not_ready(False)
        )
        self.after(UI_UPDATE_DELAY_MS, self.sync_system_state_loop)

    def sync_system_state_loop(self):
        """
        Periodically sync system state with UI and hardware.

        This loop handles:
        1. Armed LED synchronization with current zone state
        2. Alarm auto-stop when all intrusions are cleared
        """
        if not self.powered:
            return

        # 1. Sync armed LED with current zone
        self._sync_armed_led()

        # 2. Auto-stop alarm if all sensors are released
        self._auto_stop_alarm_if_all_released()

        # Schedule next sync after 500ms
        self.after(500, self.sync_system_state_loop)

    def _sync_armed_led(self):
        """Synchronize armed LED with current security zone state."""
        current_zone_id = self.ui.security_zone_number

        if current_zone_id is not None and self.configuration_manager:
            zone = self.configuration_manager.safety_zones.get(current_zone_id)
            if zone:
                self.ui.set_armed_led(zone.is_armed())

    def _auto_stop_alarm_if_all_released(self):
        """
        Automatically stop alarm if all sensors are released.

        Logic:
        - Check if alarm is currently ringing
        - Check if any sensor still detects intrusion
        - If alarm is ringing but no intrusions → return to INITIALIZED
          (automatically stops alarm and cancels countdown)
        """
        # Check if all required managers are available
        if not self.alarm_manager or not self.sensor_manager:
            return

        # If alarm is ringing
        if self.alarm_manager.is_ringing():
            # Check if any intrusion is still active
            if not self.sensor_manager.if_intrusion_detected():
                # All sensors released → return to INITIALIZED state
                self.state_manager.change_state_to(
                    ControlPanelState.INITIALIZED
                )

    def _turn_panel_off(self):
        """Turn panel off."""

        def _shutdown_system():
            """Shutdown system."""
            # Turn system off
            try:
                if not self.turn_system_off():
                    login_prefix = self.state_manager._get_login_prefix()
                    self.ui.set_display_messages(
                        "System shutdown failed",
                        "Please try again",
                        login_prefix,
                    )
                    return
            except Exception as e:
                login_prefix = self.state_manager._get_login_prefix()
                self.ui.set_display_messages(
                    "System shutdown failed", f"Error: {e}", login_prefix
                )
                return

            # Powering off
            self.state_manager.change_state_to(ControlPanelState.OFFLINE)

        # if already powered off, return
        if not self.powered:
            return

        # Cancel all timers
        self.state_manager.cancel_all_timers()

        # Display message
        self.ui.set_display_not_ready(True)
        login_prefix = self.state_manager._get_login_prefix()
        self.ui.set_display_messages(
            "Stopping system...", "Please wait...", login_prefix
        )
        self.after(UI_UPDATE_DELAY_MS, _shutdown_system)

    def _reset_panel(self):
        """Reset panel."""
        # turn panel off
        self._turn_panel_off()

        # Wait for panel to fully shut down, then reset and turn back on
        def restart_system():
            # set reset database flag to True
            self.set_reset_database(True)
            # turn panel on
            self._turn_panel_on()
            # set reset database flag to False after startup
            self.after(
                UI_UPDATE_DELAY_MS * 2, lambda: self.set_reset_database(False)
            )

        # Wait for shutdown to complete
        self.after(UI_UPDATE_DELAY_MS * 5, restart_system)

    def _panic_button_press(self):
        """Handle panic button press."""
        login_prefix = self.state_manager._get_login_prefix()
        self.ui.set_display_messages(
            "Emergency call in progress...",
            "Calling emergency phone numbers...",
            login_prefix,
        )

        # Call after delay to show the message first
        def make_calls():
            success_phone_numbers = self.external_call()
            login_prefix = self.state_manager._get_login_prefix()
            if success_phone_numbers:
                self.ui.set_display_messages(
                    "Emergency call successful",
                    f"Called to {', '.join(success_phone_numbers)}",
                    login_prefix,
                )
            else:
                self.ui.set_display_messages(
                    "Emergency call failed", "Please try again", login_prefix
                )

        self.after(UI_UPDATE_DELAY_MS * 2, make_calls)
        self.state_manager.change_state_to(ControlPanelState.PANIC_MODE)

    def _verify_login(self, id: Literal["master", "guest"]):
        """
        Verify if the user is logged in.

        Args:
            id: "master" or "guest"

        Returns:
            bool: True if the user is logged in with the given id
        """
        if not self.login_manager:
            return False

        is_logged_in = self.login_manager.is_logged_in_panel
        user_id = self.login_manager.current_user_id

        if id == "master":
            return is_logged_in and user_id == "master"
        elif id == "guest":
            return is_logged_in and user_id == "guest"
        return False

    def _check_authorization(
        self, required_role: Literal["master", "guest", "any"]
    ) -> bool:
        """
        Check if user is authorized and show error if not.

        Args:
            required_role: Required role ("master", "guest", or "any")

        Returns:
            bool: True if authorized, False otherwise
        """
        login_prefix = self.state_manager._get_login_prefix()

        if required_role == "any":
            if self._verify_login("master") or self._verify_login("guest"):
                return True
            self.ui.set_display_messages(
                "Unauthorized", "Please login first", login_prefix
            )
            return False

        if self._verify_login(required_role):
            return True

        self.ui.set_display_messages(
            "Unauthorized", f"Please login as {required_role}", login_prefix
        )
        return False

    def _get_sorted_zone_ids(self) -> List[int]:
        """Get sorted list of zone IDs."""
        return sorted(self.configuration_manager.safety_zones.keys())

    def _navigate_to_previous_zone(self) -> None:
        """Navigate to the previous security zone."""
        zone_ids = self._get_sorted_zone_ids()
        if not zone_ids:
            return

        if (
            self.ui.security_zone_number is None
            or self.ui.security_zone_number not in zone_ids
        ):
            self.ui.set_security_zone_number(zone_ids[0])
        else:
            idx = zone_ids.index(self.ui.security_zone_number) - 1
            self.ui.set_security_zone_number(zone_ids[idx])

    def _navigate_to_next_zone(self) -> None:
        """Navigate to the next security zone."""
        zone_ids = self._get_sorted_zone_ids()
        if not zone_ids:
            return

        if (
            self.ui.security_zone_number is None
            or self.ui.security_zone_number not in zone_ids
        ):
            self.ui.set_security_zone_number(zone_ids[0])
        else:
            idx = zone_ids.index(self.ui.security_zone_number) + 1
            self.ui.set_security_zone_number(zone_ids[idx % len(zone_ids)])
