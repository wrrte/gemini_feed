"""
Control Panel Input Handler.

This module handles all input processing functionality for the control panel,
including button press handling and validation logic.
"""

from typing import TYPE_CHECKING, List

from constants import MAX_LOGIN_TRIALS, UI_UPDATE_DELAY_MS
from core.control_panel.control_panel_state_manager import ControlPanelState

if TYPE_CHECKING:  # pragma: no cover
    from core.control_panel.control_panel import ControlPanel


class ControlPanelInputHandler:
    """Handles all button input processing for the control panel."""

    def __init__(self, parent: "ControlPanel"):
        """
        Initialize the input handler.

        Args:
            parent: Parent ControlPanel instance
        """
        self.parent = parent
        self.panel_id_input = ""
        self.digit_input: List[int] = []
        self.new_password_temp = ""

    def handle_button_press(self, button: str):
        """
        Handle button press.

        Args:
            button: Button identifier string
        """
        print(f"Panel state (before): {self.parent.state_manager.panel_state}")
        print(f"Button pressed: {button}")

        # if the panel is locked, return with display locked message
        if self.parent.state_manager.panel_state == ControlPanelState.LOCKED:
            return

        # if in OFFLINE
        if self.parent.state_manager.panel_state == ControlPanelState.OFFLINE:
            if button == "1":
                self.parent._turn_panel_on()
                return

        # if back button press (#), go to init state
        if (
            button == "#"
            and self.parent.state_manager.panel_state
            != ControlPanelState.OFFLINE
            and self.parent.state_manager.panel_state
            != ControlPanelState.PANEL_ID_INPUT
        ):
            self.parent.state_manager.change_state_to(
                ControlPanelState.INITIALIZED
            )
            return

        # handle panic button press
        if (
            button == "panic"
            and self.parent.state_manager.panel_state
            != ControlPanelState.OFFLINE
        ):
            self.parent._panic_button_press()
            return

        # if in initialized
        if (
            self.parent.state_manager.panel_state
            == ControlPanelState.INITIALIZED
        ):
            if button == "6":
                self.parent.state_manager.change_state_to(
                    ControlPanelState.FUNCTION_MODE
                )
                return

        # if in function mode, handle function mode button press
        if (
            self.parent.state_manager.panel_state
            == ControlPanelState.FUNCTION_MODE
        ):
            self._handle_function_mode_button_press(button)
            return

        # if in digit input, handle digit input button press
        if (
            self.parent.state_manager.panel_state
            == ControlPanelState.DIGIT_INPUT
        ):
            self._handle_digit_input_button_press(button)

        # if in panel id input, handle panel id input button press
        if (
            self.parent.state_manager.panel_state
            == ControlPanelState.PANEL_ID_INPUT
        ):
            self._handle_panel_id_input_button_press(button)

        # if in master password change, handle master password change
        input_1 = ControlPanelState.MASTER_PASSWORD_CHANGE_INPUT_1
        input_2 = ControlPanelState.MASTER_PASSWORD_CHANGE_INPUT_2
        if (
            self.parent.state_manager.panel_state == input_1
            or self.parent.state_manager.panel_state == input_2
        ):
            self._handle_master_password_change_button_press(button)

        print(f"Panel state (after): {self.parent.state_manager.panel_state}")

    def _handle_function_mode_button_press(self, button: str):
        """Handle function mode button press."""
        if button == "1":
            self.parent._turn_panel_on()
        elif button == "2":
            self.parent._turn_panel_off()
        elif button == "3":
            if not self.parent._check_authorization("master"):
                return
            self.parent._reset_panel()
        elif button == "4":
            if not self.parent._check_authorization("master"):
                return
            is_success = (
                self.parent.configuration_manager.change_to_safehome_mode(
                    "Away"
                )
            )
            if not is_success:
                self.parent.ui.set_display_messages(
                    "Failed to change to away mode",
                    "Please try again",
                )
                return
            self.parent.ui.set_display_away(True)
            self.parent.ui.set_display_home(False)
        elif button == "5":
            if not self.parent._check_authorization("master"):
                return
            is_success = (
                self.parent.configuration_manager.change_to_safehome_mode(
                    "Home"
                )
            )
            if not is_success:
                self.parent.ui.set_display_messages(
                    "Failed to change to home mode",
                    "Please try again",
                )
                return
            self.parent.ui.set_display_away(False)
            self.parent.ui.set_display_home(True)
        elif button == "6":
            return
        elif button == "7":
            if not self.parent._check_authorization("any"):
                return
            self.parent._navigate_to_previous_zone()
        elif button == "8":
            if not self.parent._check_authorization("master"):
                return
            self._toggle_current_zone_arm_state()
        elif button == "9":
            if not self.parent._check_authorization("any"):
                return
            self.parent._navigate_to_next_zone()
        elif button == "0":
            if not self.parent._check_authorization("master"):
                return
            # Start master password change process
            self.parent.state_manager.change_state_to(
                ControlPanelState.MASTER_PASSWORD_CHANGE_INPUT_1
            )
        elif button == "*":
            self.parent.state_manager.change_state_to(
                ControlPanelState.PANEL_ID_INPUT
            )
        elif button == "#":
            pass

    def _handle_digit_input_button_press(self, button: str):
        """Handle digit input button press."""
        if not button.isdigit():
            return

        self.digit_input.append(int(button))
        login_prefix = self.parent.state_manager._get_login_prefix()
        short_message2 = (
            f"Code: {''.join(str(digit) for digit in self.digit_input)}"
        )
        self.parent.ui.set_display_messages(
            short_message2, login_prefix=login_prefix
        )
        self._handle_panel_login()

    def _handle_panel_id_input_button_press(self, button: str):
        """Handle panel id input button press."""
        # init inputs
        self.digit_input = []

        if button == "*":
            self.panel_id_input = "master"
        elif button == "#":
            self.panel_id_input = "guest"
            # For guest password is null, try login without password
            if self._handle_panel_login():
                return
        else:
            return

        # get digits input
        self.parent.state_manager.change_state_to(
            ControlPanelState.DIGIT_INPUT
        )

    def _handle_master_password_change_button_press(self, button: str):
        """Handle master password change button press."""
        # Only accept digit buttons
        if not button.isdigit():
            return

        # Add digit to input
        self.digit_input.append(int(button))

        # Show masked password
        masked = "*" * len(self.digit_input)

        state_1 = ControlPanelState.MASTER_PASSWORD_CHANGE_INPUT_1
        state_2 = ControlPanelState.MASTER_PASSWORD_CHANGE_INPUT_2

        login_prefix = self.parent.state_manager._get_login_prefix()

        if self.parent.state_manager.panel_state == state_1:
            self.parent.ui.set_display_short_message2(
                f"New password: {masked}"
            )

            # If 4 digits entered, move to second input
            if len(self.digit_input) == 4:
                pwd = "".join(str(d) for d in self.digit_input)
                self.new_password_temp = pwd
                self.digit_input = []
                self.parent.state_manager.panel_state = state_2
                self.parent.ui.set_display_messages(
                    "Re-enter new password", "", login_prefix
                )

        elif self.parent.state_manager.panel_state == state_2:
            self.parent.ui.set_display_short_message2(f"Confirm: {masked}")

            # If 4 digits entered, verify and save
            if len(self.digit_input) == 4:
                confirm = "".join(str(d) for d in self.digit_input)

                if self.new_password_temp == confirm:
                    # TODO: Password change is not implemented yet
                    self.parent.ui.set_display_messages(
                        "Password changed!",
                        "Successfully updated",
                        login_prefix,
                    )
                else:
                    # Passwords don't match
                    self.parent.ui.set_display_messages(
                        "Password mismatch!", "Please try again", login_prefix
                    )

                # Reset and return to initialized state
                self.digit_input = []
                self.new_password_temp = ""

                self.parent.after(
                    UI_UPDATE_DELAY_MS * 6,
                    lambda: self.parent.state_manager.change_state_to(
                        ControlPanelState.INITIALIZED
                    ),
                )

    def _handle_panel_login(self) -> bool:
        """
        Handle panel login.

        Returns:
            bool: True if login successful
        """
        # validate input
        if len(self.digit_input) < 4 and self.panel_id_input != "guest":
            return False
        if not all(isinstance(digit, int) for digit in self.digit_input):
            self.digit_input = []
            login_prefix = self.parent.state_manager._get_login_prefix()
            self.parent.ui.set_display_short_message1(
                "Invalid input", login_prefix
            )
            self.parent.ui.set_display_short_message2(
                "Please enter a valid 4 digit number"
            )
            return False

        # try login panel
        panel_id = self.panel_id_input
        password = (
            "".join(str(digit) for digit in self.digit_input)
            if self.digit_input
            else None
        )
        if not self.parent.login_manager.login_panel(panel_id, password):
            max_trail_exceeded = (
                self.parent.login_manager.is_login_trials_exceeded()
            )
            if max_trail_exceeded:
                self.parent.state_manager.start_lock_timer()
                return False

            login_prefix = self.parent.state_manager._get_login_prefix()
            self.parent.ui.set_display_short_message1(
                "Login failed", login_prefix
            )
            trials_left = (
                MAX_LOGIN_TRIALS - self.parent.login_manager.login_trials
            )
            self.parent.ui.set_display_short_message2(
                f"Please try again (trial left: {trials_left})"
            )
            self.digit_input = []
            return False

        # login successful
        self.digit_input = []
        login_prefix = self.parent.state_manager._get_login_prefix()
        self.parent.ui.set_display_short_message1(
            "Login successful", login_prefix
        )
        self.parent.ui.set_display_short_message2("")
        self.parent.after(
            UI_UPDATE_DELAY_MS,
            lambda: self.parent.state_manager.change_state_to(
                ControlPanelState.INITIALIZED
            ),
        )
        return True

    def _toggle_current_zone_arm_state(self) -> None:
        """Toggle arm/disarm state of the current zone."""
        zone_id = self.parent.ui.security_zone_number
        if zone_id is None:
            return

        zone = self.parent.configuration_manager.safety_zones.get(zone_id)
        if not zone:
            return

        # Toggle: disarm if armed, arm if disarmed
        config_mgr = self.parent.configuration_manager
        if zone.is_armed():
            success = config_mgr.disarm_safety_zone(zone_id)
        else:
            success = config_mgr.arm_safety_zone(zone_id)

        # Update UI
        if not success:
            self.parent.ui.set_display_messages(
                "Failed to arm/disarm zone", "Please try again"
            )
            return

        self.parent.ui.set_armed_led(zone.is_armed())
