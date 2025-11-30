import customtkinter as ctk

from configurations.safety_zone import SafetyZone
from core.pages.interface_page import InterfaceWindow
from core.pages.utils import (draw_floor_plan, find_lowest_empty_id,
                              is_sensor_in_rect)
from database.schema.safety_zone import SafetyZoneSchema
from database.schema.sensor import SensorType
from manager.configuration_manager import ConfigurationManager


class ZoneConfigurationWindow(InterfaceWindow):
    """
    [Pop-up] Window for adding and modifying Zones.
    Inherits InterfaceWindow and implements draw_page.
    """

    def __init__(
        self,
        master,
        page_id: str,
        sensor_manager,
        configuration_manager: ConfigurationManager,
        on_success_callback,
        zone_id=None,
        zone_name=None,
        **kwargs,
    ):
        self.sensor_manager = sensor_manager
        self.configuration_manager = configuration_manager
        self.on_success_callback = on_success_callback
        self.target_zone_id = zone_id
        self.initial_zone_name = zone_name

        # Initialize state variables
        self.drag_start = {"x": None, "y": None}
        self.current_coords = {"x1": None, "y1": None, "x2": None, "y2": None}
        self.selected_sensors = set()
        self.display_name = ""

        # Load initial data (if editing mode)
        if zone_id:
            zone = self.configuration_manager.get_safety_zone(zone_id)
            title = "Update Security Zone"
            self.display_name = zone.get_zone_name() if zone else ""
            self._load_initial_data(zone)
        else:
            title = "Add Security Zone"
            self.display_name = zone_name or ""

        # Call parent constructor (Create Window)
        super().__init__(
            master=master,
            page_id=page_id,
            title=title,
            window_width=650,
            window_height=600,
            initially_hidden=False,
            **kwargs,
        )

        self.draw_page()

        # Popup settings (Modal)
        self.attributes("-topmost", True)
        self.transient(master)
        self.grab_set()
        self.focus_force()

    def _load_initial_data(self, zone):
        if zone:
            coords = zone.get_coordinates()
            if coords:
                self.current_coords["x1"] = coords[0]
                self.current_coords["y1"] = coords[1]
                self.current_coords["x2"] = coords[2]
                self.current_coords["y2"] = coords[3]

            sensor_ids = zone.get_sensor_list()
            if sensor_ids:
                self.selected_sensors.update(sensor_ids)

    def draw_page(self):
        # === UI Configuration ===
        main_frame = ctk.CTkFrame(self, corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title_frame = ctk.CTkFrame(
            main_frame, fg_color="transparent", height=40
        )
        title_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(
            title_frame, text="Configuring Zone", font=("Arial", 18, "bold")
        ).pack(pady=5)

        # Instructions
        ctk.CTkLabel(
            main_frame,
            text="Drag to set area. Double-click sensors to toggle.",
            font=("Arial", 12),
            text_color="gray",
        ).pack(pady=(0, 5))

        # Canvas Area
        canvas_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        canvas_frame.pack(pady=(0, 10))

        self.canvas = ctk.CTkCanvas(
            canvas_frame,
            bg="white",
            highlightthickness=0,
            width=500,
            height=312,
        )
        self.canvas.pack(padx=10, pady=10)

        # Name Input Area
        name_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        name_frame.pack(pady=(0, 10))

        ctk.CTkLabel(
            name_frame, text="Zone Name:", font=("Arial", 12, "bold")
        ).pack(side="left", padx=(0, 10))

        self.name_entry = ctk.CTkEntry(name_frame, width=200)
        self.name_entry.pack(side="left", padx=5)
        if self.display_name:
            self.name_entry.insert(0, self.display_name)

        self.name_error_label = ctk.CTkLabel(
            name_frame, text="", text_color="red"
        )
        self.name_error_label.pack(side="left", padx=10)

        # Error Message Area
        self.error_label = ctk.CTkLabel(
            main_frame, text="", text_color="red", height=0
        )
        self.error_label.pack(pady=(0, 5))

        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=5)

        ctk.CTkButton(
            button_frame, text="Confirm", width=100, command=self._confirm_zone
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=100,
            fg_color="gray",
            command=self.destroy,
        ).pack(side="left", padx=5)

        # Event Binding
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_press)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_release)
        self.canvas.bind("<Double-Button-1>", self._on_sensor_click)

        # Initial Draw
        self.after(100, self._redraw_canvas)

    def _redraw_canvas(self):
        self.canvas.delete("all")
        draw_floor_plan(self.canvas)

        for sensor in self.sensor_manager.sensor_dict.values():
            x, y = sensor.coordinate_x, sensor.coordinate_y
            sid = sensor.sensor_id

            # Determine color based on selection
            is_selected = sid in self.selected_sensors
            fill = "blue" if is_selected else "red"
            line_width = 3 if is_selected else 2

            if sensor.get_type() == SensorType.MOTION_DETECTOR_SENSOR:
                x2 = getattr(sensor, "coordinate_x2", x)
                y2 = getattr(sensor, "coordinate_y2", y)

                # Draw Line
                self.canvas.create_line(
                    x,
                    y,
                    x2,
                    y2,
                    fill=fill,
                    width=line_width,
                    tags=f"sensor_{sid}",
                )

                # Draw Endpoints
                r = 4
                self.canvas.create_oval(
                    x - r,
                    y - r,
                    x + r,
                    y + r,
                    fill=fill,
                    outline="",
                    tags=f"sensor_{sid}",
                )
                self.canvas.create_oval(
                    x2 - r,
                    y2 - r,
                    x2 + r,
                    y2 + r,
                    fill=fill,
                    outline="",
                    tags=f"sensor_{sid}",
                )

                text_x, text_y = (x + x2) / 2, (y + y2) / 2 - 10
                anchor = "center"
            else:
                # Other sensors (Circle)
                outline = "darkblue" if is_selected else "darkred"
                self.canvas.create_oval(
                    x - 5,
                    y - 5,
                    x + 5,
                    y + 5,
                    fill=fill,
                    outline=outline,
                    width=2,
                    tags=f"sensor_{sid}",
                )
                text_x, text_y = x + 10, y
                anchor = "w"

            self.canvas.create_text(
                text_x,
                text_y,
                text=f"S{sid}",
                anchor=anchor,
                font=("Arial", 8),
                tags=f"sensor_{sid}",
            )

        if None not in self.current_coords.values():
            self.canvas.create_rectangle(
                self.current_coords["x1"],
                self.current_coords["y1"],
                self.current_coords["x2"],
                self.current_coords["y2"],
                outline="#0000ff",
                width=3,
                dash=(5, 5),
            )

    def _on_mouse_press(self, event):
        self.drag_start["x"] = max(0, min(event.x, 500))
        self.drag_start["y"] = max(0, min(event.y, 312))

    def _on_mouse_drag(self, event):
        if self.drag_start["x"] is None:
            return
        ex, ey = max(0, min(event.x, 500)), max(0, min(event.y, 312))

        self.current_coords["x1"] = min(self.drag_start["x"], ex)
        self.current_coords["y1"] = min(self.drag_start["y"], ey)
        self.current_coords["x2"] = max(self.drag_start["x"], ex)
        self.current_coords["y2"] = max(self.drag_start["y"], ey)

        # Auto-select sensors in area (Using helper function)
        self.selected_sensors.clear()
        for sensor in self.sensor_manager.sensor_dict.values():
            if is_sensor_in_rect(
                sensor,
                self.current_coords["x1"],
                self.current_coords["y1"],
                self.current_coords["x2"],
                self.current_coords["y2"],
            ):
                self.selected_sensors.add(sensor.sensor_id)

        self._redraw_canvas()

    def _on_mouse_release(self, event):
        self.drag_start = {"x": None, "y": None}

    def _on_sensor_click(self, event):
        clicked = self.canvas.find_overlapping(
            event.x - 5, event.y - 5, event.x + 5, event.y + 5
        )
        for item_id in clicked:
            tags = self.canvas.gettags(item_id)
            for tag in tags:
                if tag.startswith("sensor_"):
                    sid = int(tag.split("_")[1])
                    if sid in self.selected_sensors:
                        self.selected_sensors.remove(sid)
                    else:
                        self.selected_sensors.add(sid)
                    self._redraw_canvas()
                    return

    def _confirm_zone(self):
        # check if name is valid
        name = self.name_entry.get().strip()
        if not name:
            self.name_error_label.configure(text="Name required")
            return

        # check if zone area is valid
        if None in self.current_coords.values():
            self.error_label.configure(text="Draw zone area first", height=20)
            return
        coords = (
            self.current_coords["x1"],
            self.current_coords["y1"],
            self.current_coords["x2"],
            self.current_coords["y2"],
        )

        # get selected sensors
        sensors = list(self.selected_sensors)

        # check if new zone is overlapping with any existing zone
        new_zone = SafetyZone(
            zone_id=self.target_zone_id,
            zone_name=name,
            coordinate_x1=coords[0],
            coordinate_y1=coords[1],
            coordinate_x2=coords[2],
            coordinate_y2=coords[3],
        )
        if self.configuration_manager._check_zone_is_overlap(new_zone):
            self.error_label.configure(
                text="Zone is overlapping with another zone", height=20
            )
            return

        # DB update or add new zone logic
        if self.target_zone_id:
            # [Update Existing Zone]
            self.configuration_manager.update_safety_zone(
                SafetyZoneSchema(
                    zone_id=self.target_zone_id,
                    zone_name=name,
                    coordinate_x1=coords[0],
                    coordinate_y1=coords[1],
                    coordinate_x2=coords[2],
                    coordinate_y2=coords[3],
                    sensor_id_list=sensors,
                )
            )
            z = self.configuration_manager.get_safety_zone(self.target_zone_id)
            if z:
                z.set_sensor_list(sensors)
        else:
            # [Add New Zone] with Gap Filling Logic
            # Check duplicate name
            zones = self.configuration_manager.get_all_safety_zones().values()
            for zone in zones:
                if zone.get_zone_name().lower() == name.lower():
                    self.name_error_label.configure(text="Name exists")
                    return

            # 1. Get all existing zone IDs
            existing_ids = set(
                self.configuration_manager.get_all_safety_zones().keys()
            )

            # 2. Find the smallest empty ID
            new_id = find_lowest_empty_id(existing_ids)

            # 3. Add new zone to database
            is_success = self.configuration_manager.add_safety_zone(
                SafetyZoneSchema(
                    zone_id=new_id,
                    zone_name=name,
                    coordinate_x1=coords[0],
                    coordinate_y1=coords[1],
                    coordinate_x2=coords[2],
                    coordinate_y2=coords[3],
                    sensor_id_list=sensors,
                ),
            )
            if not is_success:
                self.error_label.configure(
                    text="Failed to create zone in DB", height=20
                )
                return

            # 4. set sensors to new zone
            new_zone = self.configuration_manager.get_safety_zone(new_id)
            if new_zone:
                new_zone.set_sensor_list(sensors)

        # Call success callback
        if self.on_success_callback:
            self.on_success_callback()

        self.destroy()
