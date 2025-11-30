import customtkinter as ctk

from core.pages.interface_page import InterfacePage
from core.pages.utils import draw_floor_plan, is_sensor_in_rect, show_toast
from core.pages.zone_configuration_page import ZoneConfigurationWindow
from database.schema.sensor import SensorType
from manager.configuration_manager import ConfigurationManager
from manager.sensor_manager import SensorManager


class SecurityPage(InterfacePage):
    """
    [Main Page] Security Zone Management and Monitoring.
    """

    def __init__(
        self,
        master,
        sensor_manager: SensorManager,
        page_id,
        login_manager=None,
        configuration_manager: ConfigurationManager = None,
        **kwargs,
    ):
        super().__init__(master, page_id, **kwargs)
        self.sensor_manager = sensor_manager
        self.login_manager = login_manager
        self.configuration_manager = configuration_manager

        self._sync_sensors_to_zones()

        # Initialize rendering variables
        self._draw_job = None
        self.selected_zone_id = None
        self.zone_canvas_items = {}
        self._monitoring_active = False

        # State snapshot for anti-flickering
        self._last_state_snapshot = None

        self.draw_page()

    def tkraise(self, above_this=None):
        """Override tkraise to show authentication screen when page shown."""
        self.draw_page()
        super().tkraise(above_this)

    def _sync_sensors_to_zones(self):
        """
        Assign sensors to zones based on coordinates.
        Supports both points (WinDoor) and lines (Motion).
        """
        if not self.configuration_manager or not self.sensor_manager:
            return

        zones = self.configuration_manager.get_all_safety_zones()

        for zone in zones.values():
            coords = zone.get_coordinates()
            if not coords:
                continue

            # Unpack zone coordinates
            rx1, ry1, rx2, ry2 = coords
            sensors_in_zone = []

            for sensor in self.sensor_manager.sensor_dict.values():
                if is_sensor_in_rect(sensor, rx1, ry1, rx2, ry2):
                    sensors_in_zone.append(sensor.sensor_id)

            if sensors_in_zone:
                zone.set_sensor_list(sensors_in_zone)

    def draw_page(self):
        # Remove existing widgets
        for widget in self.winfo_children():
            widget.destroy()

        # Reset monitoring flag
        self._monitoring_active = False

        # Always show login screen first
        self._show_authentication_screen()

    def _show_authentication_screen(self):
        """Show web login authentication screen."""
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            container,
            text="Security Page Access",
            font=("Arial", 20, "bold"),
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            container,
            text="2-level Authentication: Please enter web password",
            font=("Arial", 12),
            text_color="gray",
        ).pack(pady=(0, 20))

        password_entry = ctk.CTkEntry(
            container,
            placeholder_text="Web Password",
            show="*",
            width=300,
            height=40,
            font=("Arial", 14),
        )
        password_entry.pack(pady=10)
        password_entry.focus()

        error_label = ctk.CTkLabel(
            container,
            text="",
            font=("Arial", 11),
            text_color="red",
            height=0,
        )
        error_label.pack()

        button_frame = ctk.CTkFrame(container, fg_color="transparent")
        button_frame.pack(pady=15)

        def verify_password():
            password = password_entry.get()
            if not password:
                error_label.configure(text="Please enter password", height=20)
                return

            error_label.configure(text="", height=0)

            if not self.login_manager:
                error_label.configure(
                    text="Login manager not available", height=20
                )
                return

            user_id = self.login_manager.current_user_id
            if not user_id:
                error_label.configure(text="No user logged in", height=20)
                return

            if self.login_manager._verify_web_password(user_id, password):
                for widget in self.winfo_children():
                    widget.destroy()
                self._draw_security_content()
            else:
                password_entry.delete(0, "end")
                password_entry.focus()
                error_label.configure(
                    text="Incorrect password! Try again", height=20
                )

        ctk.CTkButton(
            button_frame,
            text="Login",
            width=120,
            height=35,
            font=("Arial", 13),
            command=verify_password,
        ).pack(side="left", padx=5)

        password_entry.bind("<Return>", lambda e: verify_password())

    def _draw_security_content(self):
        """Draw actual security page content after authentication."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0, minsize=600)
        self.grid_rowconfigure(0, weight=1)

        # ===== Left Panel (Controls + Status) =====
        self.left_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.left_panel.grid_rowconfigure(0, weight=0)
        self.left_panel.grid_rowconfigure(1, weight=3)
        self.left_panel.grid_columnconfigure(0, weight=1)

        # 1. Control Section
        self.control_frame = ctk.CTkFrame(self.left_panel, corner_radius=10)
        self.control_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        ctk.CTkLabel(
            self.control_frame,
            text="Security Controls",
            font=("Arial", 16, "bold"),
        ).grid(row=0, column=0, columnspan=2, pady=10, padx=10, sticky="w")

        self.control_frame.grid_columnconfigure(0, weight=1)
        self.control_frame.grid_columnconfigure(1, weight=1)
        self.control_frame.grid_columnconfigure(2, weight=1)

        self.btn_add = ctk.CTkButton(
            self.control_frame,
            text="Add Zone",
            command=self.add_zone,
            height=35,
        )
        self.btn_add.grid(
            row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew"
        )

        self.btn_update = ctk.CTkButton(
            self.control_frame,
            text="Update Zone",
            command=self.update_zone,
            height=35,
        )
        self.btn_update.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        self.btn_delete = ctk.CTkButton(
            self.control_frame,
            text="Delete Zone",
            command=self.delete_zone,
            height=35,
        )
        self.btn_delete.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        self.btn_arm = ctk.CTkButton(
            self.control_frame,
            text="Arm Zone",
            command=self.arm_zone,
            height=35,
        )
        self.btn_arm.grid(row=3, column=0, padx=10, pady=(5, 10), sticky="ew")

        self.btn_disarm = ctk.CTkButton(
            self.control_frame,
            text="Disarm Zone",
            command=self.disarm_zone,
            height=35,
        )
        self.btn_disarm.grid(
            row=3, column=1, padx=10, pady=(5, 10), sticky="ew"
        )

        self._update_button_states()

        # 2. Status Section
        self.status_frame = ctk.CTkFrame(self.left_panel, corner_radius=10)
        self.status_frame.grid(row=1, column=0, sticky="nsew")

        ctk.CTkLabel(
            self.status_frame, text="Zone Status", font=("Arial", 16, "bold")
        ).pack(pady=10, padx=10, anchor="w")

        self.status_list = ctk.CTkScrollableFrame(
            self.status_frame, fg_color="transparent"
        )
        self.status_list.pack(fill="both", expand=True, padx=5, pady=5)

        self._update_zone_status_list()

        # ===== Right Panel (Floor Plan) =====
        self.right_panel = ctk.CTkFrame(self, corner_radius=10)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(
            self.right_panel,
            text="Floor Plan View",
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
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # Start monitoring (After successful login)
        self._monitoring_active = True
        self._start_monitoring()

    def _start_monitoring(self):
        """
        Periodically check sensor status, sync zone status,
        and refresh UI only when changes occur (Anti-flickering).
        """
        if not self.winfo_exists() or not self._monitoring_active:
            return

        # 1. Update Zone model status based on sensors
        self._sync_zone_state_with_sensors()

        # 2. Create snapshot of current state
        current_snapshot = self._get_ui_state_snapshot()

        # 3. Refresh UI only if state changed
        if current_snapshot != self._last_state_snapshot:
            self._render_content()
            self._update_zone_status_list()
            self._last_state_snapshot = current_snapshot

        # Repeat every 0.5s
        self.after(500, self._start_monitoring)

    def _get_ui_state_snapshot(self):
        """
        Returns a snapshot of data required for UI rendering.
        """
        # 1. Zone Arm status
        zone_states = {}
        if self.configuration_manager:
            for (
                zid,
                zone,
            ) in self.configuration_manager.get_all_safety_zones().items():
                zone_states[zid] = zone.is_armed()

        # 2. Sensor Arm status
        sensor_states = {}
        if self.sensor_manager:
            for sid, sensor in self.sensor_manager.sensor_dict.items():
                sensor_states[sid] = sensor.is_armed()

        # 3. Current Selection
        selection_state = self.selected_zone_id

        return (
            tuple(sorted(zone_states.items())),
            tuple(sorted(sensor_states.items())),
            selection_state,
        )

    def _sync_zone_state_with_sensors(self):
        """
        Check sensor status within each Zone:
        - Any sensor armed -> Zone Armed
        - All sensors disarmed -> Zone Disarmed
        """
        if not self.configuration_manager or not self.sensor_manager:
            return

        zones = self.configuration_manager.get_all_safety_zones()
        for zone in zones.values():
            sensor_ids = zone.get_sensor_list()
            if not sensor_ids:
                continue

            any_sensor_armed = False
            for sid in sensor_ids:
                if sid in self.sensor_manager.sensor_dict:
                    sensor = self.sensor_manager.sensor_dict[sid]
                    if sensor.is_armed():
                        any_sensor_armed = True
                        break

            if any_sensor_armed:
                zone.arm()
            else:
                zone.disarm()

    def _on_canvas_ready(self, event=None):
        if self._draw_job is not None:
            self.canvas.after_cancel(self._draw_job)
        self._draw_job = self.canvas.after(50, self._render_content)

    def _render_content(self):
        self.canvas.delete("all")
        self.zone_canvas_items.clear()
        self._draw_floor_plan()
        self._draw_security_zones()
        self._draw_sensors()

    def _draw_floor_plan(self):
        draw_floor_plan(self.canvas)

    def _draw_security_zones(self):
        if not self.configuration_manager:
            return

        zones = self.configuration_manager.get_all_safety_zones()

        for zone_id, zone in zones.items():
            coords = zone.get_coordinates()
            if not coords:
                continue

            x1, y1, x2, y2 = coords

            # Determine color based on arm status
            if zone.is_armed():
                fill_color = "#ffcccc"  # Light red for armed
                outline_color = "#ff0000"  # Red outline
            else:
                fill_color = "#6F6F6F"
                outline_color = "#000000"

            rect_id = self.canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill=fill_color,
                outline=outline_color,
                width=2,
                stipple="gray50",
                tags=("zone", f"zone_{zone_id}"),
            )

            self.zone_canvas_items[zone_id] = rect_id

            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            self.canvas.create_text(
                center_x,
                center_y,
                text=f"Zone {zone_id}\n{zone.get_zone_name()}",
                font=("Arial", 10, "bold"),
                tags=("zone", f"zone_{zone_id}"),
            )

            if zone_id == self.selected_zone_id:
                self.canvas.itemconfig(rect_id, width=4, outline="#ffff00")

    def _on_canvas_click(self, event):
        clicked_items = self.canvas.find_overlapping(
            event.x - 2, event.y - 2, event.x + 2, event.y + 2
        )

        for item_id in clicked_items:
            tags = self.canvas.gettags(item_id)
            for tag in tags:
                if tag.startswith("zone_"):
                    zone_id = int(tag.split("_")[1])
                    self._select_zone(zone_id)
                    return

        self._select_zone(None)

    def _select_zone(self, zone_id):
        self.selected_zone_id = zone_id
        # Immediate visual feedback
        self._update_zone_selection_visual()
        self._update_zone_status_list()
        self._update_button_states()

    def _update_zone_selection_visual(self):
        for zid, item_id in self.zone_canvas_items.items():
            zone = self.configuration_manager.get_safety_zone(zid)
            if zone:
                if zone.is_armed():
                    outline_color = "#ff0000"
                else:
                    outline_color = "#000000"
                self.canvas.itemconfig(item_id, width=2, outline=outline_color)

        if (
            self.selected_zone_id
            and self.selected_zone_id in self.zone_canvas_items
        ):
            item_id = self.zone_canvas_items[self.selected_zone_id]
            self.canvas.itemconfig(item_id, width=5, outline="#ffff00")

    def _draw_sensors(self):
        for sensor in self.sensor_manager.sensor_dict.values():
            x = sensor.coordinate_x
            y = sensor.coordinate_y

            fill_color = "red" if sensor.is_armed() else "#B0BEC5"
            outline_color = "black" if sensor.is_armed() else "gray60"
            line_width = 3 if sensor.is_armed() else 2

            if sensor.get_type() == SensorType.MOTION_DETECTOR_SENSOR:
                # Motion Sensor: Line
                x2 = getattr(sensor, "coordinate_x2", x)
                y2 = getattr(sensor, "coordinate_y2", y)

                self.canvas.create_line(
                    x,
                    y,
                    x2,
                    y2,
                    fill=fill_color,
                    width=line_width,
                    tags="sensor",
                )

                # Endpoints
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

                text_x = (x + x2) / 2
                text_y = (y + y2) / 2 - 10
                anchor = "center"
                sensor_text = f"M({sensor.sensor_id})"

            else:
                # Other sensors: Circle
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
                font=("Arial", 8),
                tags="sensor",
            )

    def _add_status_item(self, text, state="Normal", is_selected=False):
        item_frame = ctk.CTkFrame(
            self.status_list,
            height=100,
            fg_color="#C9C9C9" if is_selected else "transparent",
        )
        item_frame.pack(fill="x", pady=2)

        ctk.CTkLabel(
            item_frame, text=text, font=("Arial", 12), fg_color="transparent"
        ).pack(side="left", padx=10, pady=3)

        color = "#e74c3c" if state in ["Normal", "Armed"] else "#000000"
        ctk.CTkLabel(
            item_frame,
            text=state,
            font=("Arial", 12, "bold"),
            text_color=color,
            fg_color="transparent",
        ).pack(side="right", padx=10, pady=3)

    def _update_zone_status_list(self):
        for widget in self.status_list.winfo_children():
            widget.destroy()

        if not self.configuration_manager:
            return

        zones = self.configuration_manager.get_all_safety_zones()
        if not zones:
            ctk.CTkLabel(
                self.status_list,
                text="No zones configured",
                font=("Arial", 12),
                text_color="gray",
            ).pack(pady=10)
            return

        for zone_id, zone in zones.items():
            zone_name = zone.get_zone_name() or f"Zone {zone_id}"
            state = "Armed" if zone.is_armed() else "Disarmed"
            is_selected = zone_id == self.selected_zone_id

            self._add_status_item(
                f"Zone {zone_id} ({zone_name})", state, is_selected
            )

    def _update_button_states(self):
        has_selection = self.selected_zone_id is not None
        self.btn_add.configure(state="normal")
        self.btn_arm.configure(state="normal")
        self.btn_disarm.configure(state="normal")
        state = "normal" if has_selection else "disabled"
        self.btn_update.configure(state=state)
        self.btn_delete.configure(state=state)

    # === Button Handlers ===

    def add_zone(self):
        self._show_zone_config_dialog(zone_id=None, zone_name=None)

    def update_zone(self):
        if not self.selected_zone_id:
            return
        self._show_zone_config_dialog(
            zone_id=self.selected_zone_id, zone_name=None
        )

    def delete_zone(self):
        if not self.configuration_manager:
            return

        zone = self.configuration_manager.get_safety_zone(
            self.selected_zone_id
        )
        if not zone:
            return

        if self.configuration_manager.delete_safety_zone(
            self.selected_zone_id
        ):
            print(f"Deleted Zone {self.selected_zone_id}")
            self.selected_zone_id = None
            self._render_content()
            self._update_zone_status_list()
        else:
            print(f"Failed to delete Zone {self.selected_zone_id}")

    def arm_zone(self):
        """Arm the selected zone."""
        if not self.configuration_manager:
            return

        success = self.configuration_manager.arm_safety_zone(
            self.selected_zone_id
        )
        if not success:
            show_toast(self, f"Failed to arm zone {self.selected_zone_id}")
            return

        # Immediate UI update
        self._sync_zone_state_with_sensors()
        self._render_content()
        self._update_zone_status_list()
        print(f"Zone {self.selected_zone_id} is now armed.")

    def disarm_zone(self):
        """Disarm the selected zone."""
        if not self.configuration_manager:
            return

        success = self.configuration_manager.disarm_safety_zone(
            self.selected_zone_id
        )
        if not success:
            show_toast(self, f"Failed to disarm zone {self.selected_zone_id}")
            return

        # Immediate UI update
        self._sync_zone_state_with_sensors()
        self._render_content()
        self._update_zone_status_list()
        print(f"Zone {self.selected_zone_id} is now disarmed.")

    def _show_zone_config_dialog(self, zone_id=None, zone_name=None):
        # Generate unique popup ID
        pid = f"zone_conf_{zone_id}" if zone_id else "zone_conf_new"

        ZoneConfigurationWindow(
            master=self,
            page_id=pid,
            sensor_manager=self.sensor_manager,
            configuration_manager=self.configuration_manager,
            on_success_callback=self._on_zone_update_success,
            zone_id=zone_id,
            zone_name=zone_name,
        )

    def _on_zone_update_success(self):
        """Callback when saving is complete in the popup."""
        self._render_content()
        self._update_zone_status_list()
