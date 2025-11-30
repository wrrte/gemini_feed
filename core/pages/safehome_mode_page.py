from typing import Dict

import customtkinter as ctk

from core.pages.interface_page import InterfacePage
from core.pages.safehome_mode_configure_page import SafeHomeModeConfigurePage
from core.pages.utils import draw_floor_plan, show_toast
from database.schema.sensor import SensorType
from manager.configuration_manager import ConfigurationManager
from manager.sensor_manager import SensorManager


class SafeHomeModePage(InterfacePage):
    """
    [Main page] Mode management screen
    - Apply the same Grid layout as SecurityPage
    - Periodically monitor the state of SensorManager to auto-update the UI
    """

    def __init__(
        self,
        master,
        page_id: str,
        sensor_manager: SensorManager,
        configuration_manager: ConfigurationManager,
        **kwargs,
    ):
        super().__init__(master=master, page_id=page_id, **kwargs)

        self.sensor_manager = sensor_manager
        self.configuration_manager = configuration_manager
        self._draw_job = None
        self.mode_buttons: Dict[str, ctk.CTkButton] = {}

        self.draw_page()
        # Start periodic state monitoring
        self._start_monitoring()

    def _get_current_matching_mode(self):
        """
        Check the current state of sensors in SensorManager,
        Check if there is a matching mode and return its name.
        """
        if not self.sensor_manager:
            return None

        # Get the set of currently armed sensors' IDs
        current_armed_ids = set()
        for sid, sensor in self.sensor_manager.sensor_dict.items():
            if sensor.is_armed():
                current_armed_ids.add(sid)

        # Compare with defined modes
        modes = self.configuration_manager.get_all_safehome_modes()
        for mode in modes.values():
            mode_name = mode.mode_name
            sensor_ids = mode.get_sensor_list()
            if set(sensor_ids) == current_armed_ids:
                return mode_name

        return None

    def draw_page(self):
        # Remove existing widgets
        for widget in self.winfo_children():
            widget.destroy()

        self.mode_buttons.clear()

        # Configure Grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0, minsize=600)
        self.grid_rowconfigure(0, weight=1)

        # ===== Left Panel (Controls) =====
        self.left_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Container for center alignment
        control_container = ctk.CTkFrame(
            self.left_panel, fg_color="transparent"
        )
        control_container.place(relx=0.5, rely=0.5, anchor="center")

        # 1. Create mode apply buttons
        if self.configuration_manager:
            modes = self.configuration_manager.get_all_safehome_modes()
            ctk.CTkLabel(
                control_container,
                text="Apply Mode",
                font=("Arial", 14, "bold"),
                text_color="gray",
            ).pack(pady=(0, 10))

            for mode in modes.values():
                mode_name = mode.mode_name
                btn = ctk.CTkButton(
                    control_container,
                    text=f"Set '{mode_name}'",
                    font=ctk.CTkFont(size=14),
                    height=40,
                    width=220,
                    fg_color="transparent",
                    border_color="gray",
                    border_width=2,
                    text_color="gray",
                    command=lambda m=mode_name: self.apply_mode(m),
                )
                btn.pack(pady=5)
                self.mode_buttons[mode_name] = btn

            # Separator
            ctk.CTkFrame(
                control_container, height=2, fg_color="gray80", width=200
            ).pack(pady=20)

        # 2. Settings change button
        ctk.CTkButton(
            control_container,
            text="Redefine Security Modes",
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#E67E22",
            hover_color="#D35400",
            height=50,
            width=220,
            command=self.open_config_window,
        ).pack()

        # ===== Right Panel (Floor Plan) =====
        self.right_panel = ctk.CTkFrame(self, corner_radius=10)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(
            self.right_panel,
            text="Real-time Sensor Status",
            font=("Arial", 16, "bold"),
        ).pack(pady=10)

        self.canvas = ctk.CTkCanvas(
            self.right_panel,
            bg="white",
            highlightthickness=0,
            width=500,
            height=312,
        )
        self.canvas.pack(padx=10, pady=10)

        self.canvas.bind("<Configure>", self._on_canvas_ready)

    def _start_monitoring(self):
        """
        Periodically check the state of the sensor manager and update the UI.
        """
        if self.winfo_exists():
            self._update_ui_state()
            self.after(500, self._start_monitoring)

    def _update_ui_state(self):
        """Update button colors and canvas drawing
        based on the current sensor state."""
        current_active_mode = self._get_current_matching_mode()

        # 1. Update button states
        for mode_name, btn in self.mode_buttons.items():
            if mode_name == current_active_mode:
                btn.configure(
                    fg_color="#3B8ED0", text_color="white", border_width=0
                )
            else:
                btn.configure(
                    fg_color="transparent", text_color="gray", border_width=2
                )

        # 2. Update floor plan sensors
        self._render_content()

    def apply_mode(self, mode_name):
        """
        Apply a safehome mode.

        Args:
            mode_name: str - The name of the safehome mode to apply
        """
        print(f"Applying mode: {mode_name}")
        success = self.configuration_manager.change_to_safehome_mode(mode_name)
        if not success:
            show_toast(self, f"Failed to apply mode: {mode_name}")
            return

        # update UI
        self._update_ui_state()

    def _on_canvas_ready(self, event=None):
        if self._draw_job is not None:
            self.canvas.after_cancel(self._draw_job)
        self._draw_job = self.canvas.after(50, self._render_content)

    def _render_content(self):
        self.canvas.delete("all")
        draw_floor_plan(self.canvas)
        self._draw_sensors()

    def _draw_sensors(self):
        """
        Draw sensors based on their actual state in SensorManager.
        """
        if not self.sensor_manager:
            return

        for sensor in self.sensor_manager.sensor_dict.values():
            x = sensor.coordinate_x
            y = sensor.coordinate_y

            # Determine color based on Arm/Disarm state
            if sensor.is_armed():
                fill_color = "#E74C3C"  # Red (Armed)
                outline_color = "black"
                line_width = 3
            else:
                fill_color = "#B0BEC5"  # Gray (Disarmed)
                outline_color = "gray60"
                line_width = 2

            # Draw differently based on sensor type
            if sensor.get_type() == SensorType.MOTION_DETECTOR_SENSOR:
                # [Modified] Draw motion detectors as line segments
                x2 = getattr(sensor, "coordinate_x2", x)
                y2 = getattr(sensor, "coordinate_y2", y)

                # Draw line segment
                self.canvas.create_line(
                    x,
                    y,
                    x2,
                    y2,
                    fill=fill_color,
                    width=line_width,
                    tags="sensor",
                )

                # Draw small dots at both ends to mark the ends of the line
                r = 3
                self.canvas.create_oval(
                    x - r,
                    y - r,
                    x + r,
                    y + r,
                    fill=fill_color,
                    outline="",
                    tags="sensor",
                )
                self.canvas.create_oval(
                    x2 - r,
                    y2 - r,
                    x2 + r,
                    y2 + r,
                    fill=fill_color,
                    outline="",
                    tags="sensor",
                )

                # Text position is the midpoint of the line segment
                text_x = (x + x2) / 2
                text_y = (y + y2) / 2 - 10
                anchor = "center"
                sensor_text = f"M({sensor.sensor_id})"

            else:
                # [Maintained] Draw window/door sensors as circles as before
                self.canvas.create_oval(
                    x - 5,
                    y - 5,
                    x + 5,
                    y + 5,
                    fill=fill_color,
                    outline=outline_color,
                    tags="sensor",
                )
                text_x = x + 10
                text_y = y
                anchor = "w"
                sensor_text = f"W/D({sensor.sensor_id})"

            self.canvas.create_text(
                text_x,
                text_y,
                text=sensor_text,
                anchor=anchor,
                font=("Arial", 9, "bold"),
                tags="sensor",
            )

    def open_config_window(self):
        # Get current active mode to set as default in the config window
        current_mode = self._get_current_matching_mode()

        SafeHomeModeConfigurePage(
            master=self,
            page_id="mode_config_popup",
            sensor_manager=self.sensor_manager,
            configuration_manager=self.configuration_manager,
            current_mode_name=current_mode,
            title="Configure Security Modes",
            initially_hidden=False,
        ).tkraise()
