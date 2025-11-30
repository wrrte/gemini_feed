from typing import Dict

import customtkinter as ctk

from core.pages.interface_page import InterfaceWindow
from core.pages.utils import show_toast
from database.schema.sensor import SensorType
from manager.configuration_manager import ConfigurationManager
from manager.sensor_manager import SensorManager


class SafeHomeModeConfigurePage(InterfaceWindow):
    """
    [Popup Window] Window for changing sensor configuration per security mode
    """

    def __init__(
        self,
        master,
        page_id: str,
        sensor_manager: SensorManager,
        configuration_manager: ConfigurationManager,
        current_mode_name: str = "Away",
        title: str = "Redefine Security Modes",
        **kwargs,
    ):
        super().__init__(
            master=master,
            page_id=page_id,
            title=title,
            window_width=500,
            window_height=750,
            **kwargs,
        )

        self.sensor_manager = sensor_manager
        self.configuration_manager = configuration_manager

        self.selected_mode_name = ctk.StringVar(value=current_mode_name)
        self.sensor_check_dict: Dict[int, ctk.BooleanVar] = {}

        self.resizable(False, False)
        self.draw_page()

    def draw_page(self):
        # 1. Header & Mode Selection
        top_frame = ctk.CTkFrame(self, height=80, fg_color="transparent")
        top_frame.pack(side="top", fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            top_frame,
            text="Security Mode Configuration",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="top", anchor="w")

        ctk.CTkLabel(
            top_frame,
            text="Select Mode to Redefine:",
            font=ctk.CTkFont(size=14),
        ).pack(side="left", pady=(10, 0))

        mode_list = (
            self.configuration_manager.get_all_safehome_modes().values()
        )
        mode_names = [mode.get_mode_name() for mode in mode_list]

        self.mode_selector = ctk.CTkOptionMenu(
            top_frame,
            variable=self.selected_mode_name,
            values=mode_names,
            command=self._on_mode_change,
            width=150,
        )
        self.mode_selector.pack(side="left", padx=15, pady=(10, 0))

        if mode_names:
            self.selected_mode_name.set(mode_names[0])

        # 2. Action Buttons (Save/Return)
        action_frame = ctk.CTkFrame(self, height=60, fg_color="transparent")
        action_frame.pack(side="bottom", fill="x", padx=20, pady=20)

        ctk.CTkButton(
            action_frame,
            text="Save Configuration",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#388E3C",
            hover_color="#2E7D32",
            height=40,
            command=self._save_configuration,
        ).pack(side="right", padx=10)

        ctk.CTkButton(
            action_frame,
            text="Reset / Reload",
            font=ctk.CTkFont(size=14),
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            height=40,
            command=self._refresh_sensor_list,
        ).pack(side="right", padx=10)

        # 3. Sensor List Area
        list_container = ctk.CTkFrame(self)
        list_container.pack(
            side="top", fill="both", expand=True, padx=20, pady=10
        )

        ctk.CTkLabel(
            list_container,
            text="Select sensors to be ACTIVE in this mode:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(padx=10, pady=10, anchor="w")

        self.scroll_frame = ctk.CTkScrollableFrame(list_container)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._refresh_sensor_list()

    def _on_mode_change(self, selected_mode):
        self._refresh_sensor_list()

    def _refresh_sensor_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        self.sensor_check_dict.clear()

        self.scroll_frame.grid_columnconfigure(0, weight=1)  # WinDoor
        self.scroll_frame.grid_columnconfigure(1, weight=0)  # Separator
        self.scroll_frame.grid_columnconfigure(2, weight=1)  # Motion

        current_mode_name = self.selected_mode_name.get()
        # Get active sensors for the current mode
        modes = self.configuration_manager.get_all_safehome_modes()
        active_sensors_in_mode = []
        for mode_obj in modes.values():
            if mode_obj.get_mode_name() == current_mode_name:
                active_sensors_in_mode = mode_obj.get_sensor_list()
                break

        windoor_sensors = []
        motion_sensors = []

        if self.sensor_manager:
            for sid, sensor in self.sensor_manager.sensor_dict.items():
                stype = sensor.get_type()
                if stype == SensorType.WINDOOR_SENSOR:
                    windoor_sensors.append((sid, sensor))
                elif stype == SensorType.MOTION_DETECTOR_SENSOR:
                    motion_sensors.append((sid, sensor))

        windoor_sensors.sort(key=lambda x: x[0])
        motion_sensors.sort(key=lambda x: x[0])

        rows_windoor = 1 + len(windoor_sensors)
        rows_motion = 1 + len(motion_sensors)
        total_rows = max(rows_windoor, rows_motion)

        separator = ctk.CTkFrame(
            self.scroll_frame, width=2, fg_color="gray40", corner_radius=0
        )
        separator.grid(
            row=0,
            column=1,
            rowspan=total_rows if total_rows > 0 else 1,
            sticky="ns",
            pady=10,
        )

        ctk.CTkLabel(
            self.scroll_frame,
            text="-- Windoor Sensors --",
            font=ctk.CTkFont(weight="bold", size=13),
        ).grid(row=0, column=0, pady=(10, 15))

        for i, (sid, sensor) in enumerate(windoor_sensors):
            is_active = sid in active_sensors_in_mode
            chk_var = ctk.BooleanVar(value=is_active)
            self.sensor_check_dict[sid] = chk_var

            r = 1 + i
            c = 0
            self._create_sensor_checkbox(sid, chk_var, r, c)

        ctk.CTkLabel(
            self.scroll_frame,
            text="-- Motion Sensors --",
            font=ctk.CTkFont(weight="bold", size=13),
        ).grid(row=0, column=2, pady=(10, 15))

        for i, (sid, sensor) in enumerate(motion_sensors):
            is_active = sid in active_sensors_in_mode
            chk_var = ctk.BooleanVar(value=is_active)
            self.sensor_check_dict[sid] = chk_var

            r = 1 + i
            c = 2
            self._create_sensor_checkbox(sid, chk_var, r, c)

    def _create_sensor_checkbox(self, sid, var, row, col):
        frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        frame.grid(row=row, column=col, sticky="w", padx=30, pady=5)

        chk = ctk.CTkCheckBox(
            frame, text="", variable=var, font=ctk.CTkFont(size=12), width=80
        )

        def update_text():
            state_text = "Active" if var.get() else "Deactive"
            chk.configure(text=f"ID {sid}: {state_text}")

        update_text()
        chk.configure(command=update_text)
        chk.pack(side="left")

    def _save_configuration(self):
        current_mode_name = self.selected_mode_name.get()
        new_config_list = []

        for sid, var in self.sensor_check_dict.items():
            if var.get():
                new_config_list.append(sid)

        if not self.configuration_manager:
            show_toast(self, "Saved locally (Manager not connected).")
            return

        try:
            target_mode = self.configuration_manager.get_safehome_mode_by_name(
                current_mode_name
            )
            if target_mode is None:
                show_toast(
                    self, f"Error: Mode '{current_mode_name}' not found in DB."
                )
                return

            target_mode.set_sensor_list(new_config_list)

            success = self.configuration_manager.update_safehome_mode(
                target_mode.to_schema()
            )
            if success:
                show_toast(self, f"Success: '{current_mode_name}' saved.")
            else:
                show_toast(
                    self, "Warning: Saved locally, but DB update failed."
                )

        except Exception as e:
            print(f"Error saving mode config: {e}")
            show_toast(self, f"Error: {e}")
