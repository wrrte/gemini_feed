#!/usr/bin/env python3
"""
All Sensors Example (CustomTkinter Version - Refactored for Single Dictionary)
===================
Updated to use 'Sensors' dictionary and 'SensorType' for identification.
"""

import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
from ratelimit import RateLimitException, limits

from core.pages.interface_page import InterfaceWindow
# Import to check SensorType (adjust path according to project structure)
from database.schema.sensor import SensorType
from manager.sensor_manager import SensorManager


class SensorsManagementPage(InterfaceWindow):
    def __init__(
        self,
        master,
        page_id: str,
        sensor_manager: SensorManager,
        title: str = "Sensor Management Window",
        **kwargs,
    ):
        super().__init__(
            master=master,
            page_id=page_id,
            title=title,
            window_width=540,
            window_height=750,
            **kwargs,
        )

        self.sensor_manager = sensor_manager

        self.resizable(False, False)

        wd_ids = [
            sid
            for sid, s in self.sensor_manager.sensor_dict.items()
            if s.get_type() == SensorType.WINDOOR_SENSOR
        ]
        md_ids = [
            sid
            for sid, s in self.sensor_manager.sensor_dict.items()
            if s.get_type() == SensorType.MOTION_DETECTOR_SENSOR
        ]

        self.rangeSensorID_WinDoorSensor = tk.StringVar(value="N/A")
        self.inputSensorID_WinDoorSensor = tk.StringVar()

        self.rangeSensorID_MotionDetector = tk.StringVar(value="N/A")
        self.inputSensorID_MotionDetector = tk.StringVar()

        if wd_ids:
            self.rangeSensorID_WinDoorSensor.set(
                f"{min(wd_ids)}-{max(wd_ids)}"
            )
        else:
            self.rangeSensorID_WinDoorSensor.set("None")

        if md_ids:
            self.rangeSensorID_MotionDetector.set(
                f"{min(md_ids)}-{max(md_ids)}"
            )
        else:
            self.rangeSensorID_MotionDetector.set("None")

        self.draw_page()  # Call screen drawing function

    def draw_page(self):
        # ==============================
        # WinDoor Panel
        # ==============================
        wd_frame = ctk.CTkFrame(self, width=240, height=250)
        wd_frame.place(x=15, y=15)
        wd_frame.grid_propagate(False)
        wd_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            wd_frame,
            text="WinDoor Sensor",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, pady=(10, 5))

        ctk.CTkLabel(wd_frame, text="ID range:").grid(
            row=1, column=0, sticky="e", padx=5
        )
        ctk.CTkEntry(
            wd_frame,
            textvariable=self.rangeSensorID_WinDoorSensor,
            state="readonly",
            width=100,
        ).grid(row=1, column=1, sticky="w", padx=5, pady=2)

        ctk.CTkLabel(wd_frame, text="Input ID:").grid(
            row=2, column=0, sticky="e", padx=5
        )
        ctk.CTkEntry(
            wd_frame, textvariable=self.inputSensorID_WinDoorSensor, width=100
        ).grid(row=2, column=1, sticky="w", padx=5, pady=2)

        # Buttons
        ctk.CTkLabel(
            wd_frame, text="Sensor Control", font=ctk.CTkFont(size=11)
        ).grid(row=3, column=0, columnspan=2, pady=(5, 0))

        ctk.CTkButton(
            wd_frame,
            text="Arm",
            width=80,
            height=24,
            command=lambda: self._handle_sensor_action("windoor", "arm"),
        ).grid(row=4, column=0, padx=5, pady=2)
        ctk.CTkButton(
            wd_frame,
            text="Disarm",
            width=80,
            height=24,
            fg_color="gray",
            hover_color="darkgray",
            command=lambda: self._handle_sensor_action("windoor", "disarm"),
        ).grid(row=4, column=1, padx=5, pady=2)

        ctk.CTkLabel(
            wd_frame, text="Intrusion Simulation", font=ctk.CTkFont(size=11)
        ).grid(row=5, column=0, columnspan=2, pady=(5, 0))

        ctk.CTkButton(
            wd_frame,
            text="Intrude",
            width=80,
            height=24,
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            command=lambda: self._handle_physical_action("windoor", "intrude"),
        ).grid(row=6, column=0, padx=5, pady=(2, 10))
        ctk.CTkButton(
            wd_frame,
            text="Release",
            width=80,
            height=24,
            fg_color="#388E3C",
            hover_color="#2E7D32",
            command=lambda: self._handle_physical_action("windoor", "release"),
        ).grid(row=6, column=1, padx=5, pady=(2, 10))

        # ==============================
        # Motion Panel
        # ==============================
        md_frame = ctk.CTkFrame(self, width=240, height=250)
        md_frame.place(x=265, y=15)
        md_frame.grid_propagate(False)
        md_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            md_frame,
            text="Motion Detector",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, pady=(10, 5))

        ctk.CTkLabel(md_frame, text="ID range:").grid(
            row=1, column=0, sticky="e", padx=5
        )
        ctk.CTkEntry(
            md_frame,
            textvariable=self.rangeSensorID_MotionDetector,
            state="readonly",
            width=100,
        ).grid(row=1, column=1, sticky="w", padx=5, pady=2)

        ctk.CTkLabel(md_frame, text="Input ID:").grid(
            row=2, column=0, sticky="e", padx=5
        )
        ctk.CTkEntry(
            md_frame, textvariable=self.inputSensorID_MotionDetector, width=100
        ).grid(row=2, column=1, sticky="w", padx=5, pady=2)

        # Buttons
        ctk.CTkLabel(
            md_frame, text="Sensor Control", font=ctk.CTkFont(size=11)
        ).grid(row=3, column=0, columnspan=2, pady=(5, 0))

        ctk.CTkButton(
            md_frame,
            text="Arm",
            width=80,
            height=24,
            command=lambda: self._handle_sensor_action("motion", "arm"),
        ).grid(row=4, column=0, padx=5, pady=2)
        ctk.CTkButton(
            md_frame,
            text="Disarm",
            width=80,
            height=24,
            fg_color="gray",
            hover_color="darkgray",
            command=lambda: self._handle_sensor_action("motion", "disarm"),
        ).grid(row=4, column=1, padx=5, pady=2)

        ctk.CTkLabel(
            md_frame, text="Intrusion Simulation", font=ctk.CTkFont(size=11)
        ).grid(row=5, column=0, columnspan=2, pady=(5, 0))

        ctk.CTkButton(
            md_frame,
            text="Intrude",
            width=80,
            height=24,
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            command=lambda: self._handle_physical_action("motion", "intrude"),
        ).grid(row=6, column=0, padx=5, pady=(2, 10))
        ctk.CTkButton(
            md_frame,
            text="Release",
            width=80,
            height=24,
            fg_color="#388E3C",
            hover_color="#2E7D32",
            command=lambda: self._handle_physical_action("motion", "release"),
        ).grid(row=6, column=1, padx=5, pady=(2, 10))

        # ==============================
        # Status Display Frame
        # ==============================
        status_frame = ctk.CTkFrame(self, width=490, height=360)
        status_frame.place(x=15, y=280)
        status_frame.pack_propagate(False)

        # WinDoor Status
        ctk.CTkLabel(
            status_frame,
            text="Window/Door Sensors Status:",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(10, 0))
        self.wd_status_text = ctk.CTkTextbox(
            status_frame,
            height=150,
            font=ctk.CTkFont(family="Courier", size=12),
            state="disabled",
        )
        self.wd_status_text.pack(padx=10, pady=(5, 10), fill="x")

        # Motion Status
        ctk.CTkLabel(
            status_frame,
            text="Motion Detectors Status:",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(0, 0))
        self.motion_status_text = ctk.CTkTextbox(
            status_frame,
            height=100,
            font=ctk.CTkFont(family="Courier", size=12),
            state="disabled",
        )
        self.motion_status_text.pack(padx=10, pady=(5, 10), fill="x")

        # ==============================
        # Global Control Frame
        # ==============================
        global_frame = ctk.CTkFrame(self, width=490, height=60)
        global_frame.place(x=15, y=660)
        global_frame.grid_propagate(False)
        global_frame.grid_columnconfigure((0, 1), weight=1)
        global_frame.grid_rowconfigure(0, weight=1)

        ctk.CTkButton(
            global_frame,
            text="Arm All Sensors",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            fg_color="#1F6AA5",
            command=lambda: self._handle_all_sensors("arm"),
        ).grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkButton(
            global_frame,
            text="Disarm All Sensors",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            fg_color="gray",
            hover_color="darkgray",
            command=lambda: self._handle_all_sensors("disarm"),
        ).grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # Start status update loop
        self._update_status()

    def _handle_all_sensors(self, action: str):
        if action == "arm":
            self.sensor_manager.arm_all_sensors()
        else:
            self.sensor_manager.disarm_all_sensors()
        self._update_status()

    def _update_status(self):
        """
        Display status in the window by distinguishing types
        from the unified Sensors dictionary.
        """
        try:
            # 1. Initialize text boxes
            self.wd_status_text.configure(state="normal")
            self.wd_status_text.delete("0.0", "end")
            self.motion_status_text.configure(state="normal")
            self.motion_status_text.delete("0.0", "end")

            wd_count = 0
            md_count = 0

            # 2. Iterate through unified sensor list
            if self.sensor_manager.sensor_dict:
                for sensor_id, sensor in sorted(
                    self.sensor_manager.sensor_dict.items()
                ):
                    # Check common status
                    if callable(getattr(sensor, "test_armed_state", None)):
                        armed = sensor.test_armed_state()
                    else:
                        armed = getattr(sensor, "armed", False)

                    sensor_status = "🟢 ON " if armed else "🔴 OFF"

                    # Branch processing by type
                    if sensor.get_type() == SensorType.WINDOOR_SENSOR:
                        wd_count += 1
                        # WinDoor specific status (opened/detected, etc.)
                        # According to sensor.py, self.detected becomes True
                        # upon intrude()
                        is_open = getattr(sensor, "detected", False)
                        door_status = "🚪 OPEN  " if is_open else "🚪 CLOSED"

                        self.wd_status_text.insert(
                            "end",
                            f"ID {sensor_id}: Sensor[{sensor_status}] "
                            f"Door[{door_status}]\n",
                        )

                    elif (
                        sensor.get_type() == SensorType.MOTION_DETECTOR_SENSOR
                    ):
                        md_count += 1
                        is_detected = getattr(sensor, "detected", False)
                        motion_status = (
                            "👁️ DETECTED" if is_detected else "⚪ CLEAR"
                        )

                        self.motion_status_text.insert(
                            "end",
                            f"ID {sensor_id}: Sensor[{sensor_status}] "
                            f"Motion[{motion_status}]\n",
                        )

            # 3. Display message if no sensors exist
            if wd_count == 0:
                self.wd_status_text.insert("end", "No WinDoor sensors found\n")
            if md_count == 0:
                self.motion_status_text.insert(
                    "end", "No Motion detectors found\n"
                )

            self.wd_status_text.configure(state="disabled")
            self.motion_status_text.configure(state="disabled")

        except Exception as e:
            print(f"Error updating status: {e}")

        self.after(500, self._update_status)

    def _validate_digits(self, s: str) -> bool:
        return s.isdigit() if s else False

    def _get_target_sensor(self, category: str):
        """
        Retrieve ID from input field, validate,
        and return sensor object.
        """
        if category == "windoor":
            input_val = self.inputSensorID_WinDoorSensor.get()
            target_type = SensorType.WINDOOR_SENSOR
        else:
            input_val = self.inputSensorID_MotionDetector.get()
            target_type = SensorType.MOTION_DETECTOR_SENSOR

        if not input_val:
            messagebox.showinfo("Info", f"Input the {category} ID")
            return None, None

        if not self._validate_digits(input_val):
            messagebox.showinfo("Info", "Only digits allowed")
            return None, None

        sensor_id = int(input_val)

        # Lookup in unified dictionary
        sensor = self.sensor_manager.sensor_dict.get(sensor_id)

        if sensor is None:
            messagebox.showinfo("Info", f"ID {sensor_id} does not exist")
            return None, None

        # Type check (Important: Prevent manipulation of other sensor types)
        if sensor.get_type() != target_type:
            messagebox.showinfo(
                "Error", f"ID {sensor_id} is not a {category} sensor"
            )
            return None, None

        return sensor_id, sensor

    def _handle_sensor_action(self, category: str, action: str):
        """Handle Arm/Disarm (use unified method)."""
        sensor_id, sensor = self._get_target_sensor(category)
        if sensor:
            if action == "arm":
                self.sensor_manager.arm_sensor(sensor_id)
            else:
                self.sensor_manager.disarm_sensor(sensor_id)
            self._update_status()

    @limits(calls=1, period=1)  # Can be called only once per second
    def _execute_physical_action(self, category: str, action: str):
        """
        Execute the actual physical action (rate-limited).

        Args:
            category: Sensor category ("windoor" or "motion")
            action: Action to perform ("intrude" or "release")
        """
        sensor_id, sensor = self._get_target_sensor(category)
        if sensor:
            if action == "intrude":
                self.sensor_manager.intrude_sensor(sensor_id)
            elif action == "release":
                self.sensor_manager.release_sensor(sensor_id)
            self._update_status()

    def _handle_physical_action(self, category: str, action: str):
        """
        Handle Intrude/Release actions with rate limiting.
        (Simulate direct sensor intrusion and release).

        Cooldown: 1 second - prevents excessive clicking

        Args:
            category: Sensor category ("windoor" or "motion")
            action: Action to perform ("intrude" or "release")
        """
        try:
            self._execute_physical_action(category, action)
        except RateLimitException:
            messagebox.showwarning(
                "Cooldown Active",
                "Please wait 1 second before clicking again.",
            )
