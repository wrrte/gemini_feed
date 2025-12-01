"""
Control Panel UI Component.

This module handles all UI-related functionality for the control panel,
including drawing widgets and updating display elements.
"""

from typing import TYPE_CHECKING, Callable

import customtkinter as ctk

from constants import COLOR_ARMED

if TYPE_CHECKING:  # pragma: no cover
    from core.control_panel.control_panel import ControlPanel


class ControlPanelUI:
    """Manages all UI elements and display updates for the control panel."""

    def __init__(self, parent: "ControlPanel", width: int, height: int):
        """
        Initialize the UI component.

        Args:
            parent: Parent ControlPanel window
            width: Window width
            height: Window height
        """
        self.parent = parent
        self.width = width
        self.height = height
        self.security_zone_number = None
        self.short_message1 = ""
        self.short_message2 = ""

        # UI widget references (will be created in draw_page)
        self.control_panel_frame = None
        self.display_number = None
        self.display_away = None
        self.display_home = None
        self.display_not_ready = None
        self.display_text = None
        self.led_armed = None
        self.led_power = None

    def draw_page(self, on_button_press: Callable[[str], None]):
        """
        Draw the control panel UI elements.

        Args:
            on_button_press: Callback function for button press events
        """
        x_start = 15
        y_start = 15
        x_w1 = 100
        x_w2 = 50
        x_w3 = 100
        y_h1 = 90
        y_h2 = 110

        # Text display area (Background)
        # Placed first to ensure it stays behind other display elements
        self.control_panel_frame = ctk.CTkFrame(
            self.parent,
            width=x_w1 + x_w2 + x_w3,
            height=y_h1 + y_h2,
            fg_color="white",
            border_width=0,
        )
        self.control_panel_frame.place(x=x_start, y=y_start)

        # Security Zone label
        # Enhanced visibility with border
        display_zone_label = ctk.CTkLabel(
            self.control_panel_frame,
            width=x_w1,
            height=y_h1,
            text="Security\nZone",
            justify="center",
            fg_color="white",
            text_color="black",
            font=("Arial", 14, "bold"),
            corner_radius=0,
        )
        display_zone_label.place(x=0, y=0)

        # Zone number display (larger font, more prominent)
        self.display_number = ctk.CTkEntry(
            self.control_panel_frame,
            width=x_w2,
            height=y_h1,
            justify="center",
            fg_color="white",
            text_color="black",
            font=("Arial", 24, "bold"),
            border_width=0,
            corner_radius=0,
        )
        self.display_number.insert(0, "1")
        self.display_number.configure(state="readonly")
        self.display_number.place(x=x_w1, y=0)

        # Status displays frame
        status_frame = ctk.CTkFrame(
            self.control_panel_frame,
            width=x_w3,
            height=y_h1,
            fg_color="white",
            border_width=0,
            corner_radius=0,
        )
        status_frame.place(x=x_w1 + x_w2, y=0)

        self.display_away = ctk.CTkEntry(
            status_frame,
            justify="center",
            fg_color="white",
            text_color="light gray",
            width=x_w3,
            border_width=0,
            corner_radius=0,
        )
        self.display_away.insert(0, "away")
        self.display_away.configure(state="readonly")
        self.display_away.pack(side="top", fill="x", expand=True)

        self.display_home = ctk.CTkEntry(
            status_frame,
            justify="center",
            fg_color="white",
            text_color="light gray",
            width=x_w3,
            border_width=0,
            corner_radius=0,
        )
        self.display_home.insert(0, "home")
        self.display_home.configure(state="readonly")
        self.display_home.pack(side="top", fill="x", expand=True)

        self.display_not_ready = ctk.CTkEntry(
            status_frame,
            justify="center",
            fg_color="white",
            text_color="light gray",
            width=x_w3,
            border_width=0,
            corner_radius=0,
        )
        self.display_not_ready.insert(0, "not ready")
        self.display_not_ready.configure(state="readonly")
        self.display_not_ready.pack(side="top", fill="x", expand=True)

        # Text display area
        self.display_text = ctk.CTkTextbox(
            self.control_panel_frame,
            width=x_w1 + x_w2 + x_w3,
            height=y_h2,
            fg_color="white",
            text_color="black",
            wrap="word",
        )
        self.display_text.place(x=0, y=y_h1)
        self._update_display_text()

        # Button grid panel
        self._draw_btn_grid(on_button_press)

        # LED panel
        # Pull LED panel to the left for alignment (below Security Zone)
        led_frame = ctk.CTkFrame(
            self.parent, width=230, height=70, fg_color="transparent"
        )
        led_frame.place(x=30, y=y_start + y_h1 + y_h2)

        ctk.CTkLabel(led_frame, text="armed").grid(row=0, column=0)
        ctk.CTkLabel(led_frame, text="").grid(row=0, column=1)
        ctk.CTkLabel(led_frame, text="power").grid(row=0, column=2)

        # Use Labels for LEDs — Provides reliable color updates
        self.led_armed = ctk.CTkLabel(
            led_frame,
            text="",
            fg_color="light gray",
            width=60,
            height=20,
            corner_radius=5,
        )
        self.led_armed.grid(row=1, column=0)

        ctk.CTkLabel(led_frame, text="").grid(row=1, column=1)

        self.led_power = ctk.CTkLabel(
            led_frame,
            text="",
            fg_color="light gray",
            width=60,
            height=20,
            corner_radius=5,
        )
        self.led_power.grid(row=1, column=2)

    def _draw_btn_grid(self, on_button_press: Callable[[str], None]):
        """
        Draw the button grid.

        Args:
            on_button_press: Callback function for button press events
        """
        # Button panel with grid layout
        button_frame = ctk.CTkFrame(
            self.parent, width=240, height=300, fg_color="transparent"
        )
        button_frame.place(x=300, y=6)

        # Create button grid (8 rows x 5 columns)
        # Row 0: 1, 2, 3
        self._draw_btn(button_frame, "1", lambda: on_button_press("1"), 0, 0)
        self._draw_btn(button_frame, "2", lambda: on_button_press("2"), 0, 2)
        self._draw_btn(button_frame, "3", lambda: on_button_press("3"), 0, 4)
        self._draw_btn_label(button_frame, "on", 1, 0)
        self._draw_btn_label(button_frame, "off", 1, 2)
        self._draw_btn_label(button_frame, "reset", 1, 4)

        # Row 2: 4, 5, 6
        self._draw_btn(button_frame, "4", lambda: on_button_press("4"), 2, 0)
        self._draw_btn(button_frame, "5", lambda: on_button_press("5"), 2, 2)
        self._draw_btn(button_frame, "6", lambda: on_button_press("6"), 2, 4)
        self._draw_btn_label(button_frame, "away", 4, 0)
        self._draw_btn_label(button_frame, "home", 4, 2)
        self._draw_btn_label(button_frame, "code", 4, 4)

        # Row 5: 7, 8, 9
        self._draw_btn(button_frame, "7", lambda: on_button_press("7"), 5, 0)
        self._draw_btn(button_frame, "8", lambda: on_button_press("8"), 5, 2)
        self._draw_btn(button_frame, "9", lambda: on_button_press("9"), 5, 4)
        self._draw_btn_label(button_frame, "zone -", 6, 0)
        self._draw_btn_label(button_frame, "A/DA", 6, 2)
        self._draw_btn_label(button_frame, "zone +", 6, 4)

        # Row 7: *, 0, #
        self._draw_btn(button_frame, "*", lambda: on_button_press("*"), 7, 0)
        self._draw_btn(button_frame, "0", lambda: on_button_press("0"), 7, 2)
        self._draw_btn(button_frame, "#", lambda: on_button_press("#"), 7, 4)
        self._draw_btn_label(button_frame, "login", 8, 0)
        self._draw_btn_label(button_frame, "ChgPwd", 8, 2)
        self._draw_btn_label(button_frame, "back", 8, 4)

        # Row 9: Panic Button (full width)
        ctk.CTkButton(
            button_frame,
            text="PANIC",
            fg_color="red",
            text_color="white",
            hover_color="darkred",
            command=lambda: on_button_press("panic"),
            height=40,
        ).grid(row=9, column=0, columnspan=5, sticky="ew", pady=(0, 0))

    def _draw_btn(self, button_frame, text, command, row, column):
        """Draw a button."""
        ctk.CTkButton(
            button_frame,
            text=text,
            fg_color="white",
            text_color="black",
            hover_color="lightgray",
            command=command,
            width=40,
        ).grid(row=row, column=column)
        ctk.CTkLabel(button_frame, text="", anchor="n").grid(
            row=row, column=column + 1
        )

    def _draw_btn_label(self, button_frame, text, row, column):
        """Draw a label."""
        ctk.CTkLabel(button_frame, text=text, anchor="n").grid(
            row=row, column=column, pady=(0, 5)
        )

    def _update_display_text(self):
        """Update the display text area with current messages."""
        self.display_text.delete("1.0", "end")
        text = f"\n{self.short_message1}\n{self.short_message2}"
        self.display_text.insert("1.0", text)

    def set_security_zone_number(self, num):
        """Set the security zone number display."""
        self.security_zone_number = num
        self.display_number.configure(state="normal")
        self.display_number.delete(0, "end")
        self.display_number.insert(0, str(num))
        self.display_number.configure(state="readonly")

    def set_display_away(self, on):
        """Set the 'away' display state."""
        self.display_away.configure(text_color="black" if on else "light gray")

    def set_display_home(self, on):
        """Set the 'home' display state."""
        self.display_home.configure(text_color="black" if on else "light gray")

    def set_display_not_ready(self, on):
        """Set the 'not ready' display state."""
        self.display_not_ready.configure(
            text_color="black" if on else "light gray"
        )

    def set_display_short_message1(self, message, login_prefix=""):
        """
        Set the first short message line.

        Args:
            message: Message to display
            login_prefix: Login status prefix (e.g., "(master)", "(guest)")
        """
        full_message = f"{login_prefix}{message}" if login_prefix else message
        self.short_message1 = full_message
        self._update_display_text()

    def set_display_short_message2(self, message):
        """Set the second short message line."""
        self.short_message2 = ": " + message if message else ""
        self._update_display_text()

    def set_display_messages(
        self, msg1: str, msg2: str = "", login_prefix: str = ""
    ) -> None:
        """
        Set both display messages at once.

        Args:
            msg1: First message line
            msg2: Second message line
            login_prefix: Login status prefix
        """
        self.set_display_short_message1(msg1, login_prefix)
        self.set_display_short_message2(msg2)

    def set_armed_led(self, on):
        """Set the armed LED state."""
        self.led_armed.configure(fg_color=COLOR_ARMED if on else "light gray")

    def set_powered_led(self, on):
        """Set the power LED state."""
        self.led_power.configure(fg_color="lightgreen" if on else "light gray")
