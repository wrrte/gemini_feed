import os

import customtkinter as ctk
from PIL import Image, ImageTk

from database.schema.sensor import SensorType


def draw_floor_plan(canvas: ctk.CTkCanvas):
    """Draw the floor plan on the canvas using original image size (500x312).

    Canvas should be exactly 500x312 to match image size.
    Padding and centering should be handled by the parent container.

    Args:
        canvas: The canvas to draw on (should be 500x312)
    """
    # Clear previous drawings
    canvas.delete("all")

    # Fill canvas with white background
    canvas.create_rectangle(0, 0, 500, 312, fill="white", outline="")

    # Resolve floorplan image path: src/img/floorplan.png
    src_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    image_path = os.path.join(src_dir, "img", "floorplan.png")

    try:
        img = Image.open(image_path).convert("RGBA")
        # img size should be 500x312

        # Keep a reference on the canvas to avoid garbage collection
        canvas._floor_img_tk = ImageTk.PhotoImage(img)

        # Draw image at (0, 0) - no offset needed
        # Sensor coordinates from DB can be used directly
        canvas.create_image(0, 0, image=canvas._floor_img_tk, anchor="nw")

    except Exception as e:
        # Fallback: draw a simple placeholder
        canvas.create_rectangle(5, 5, 495, 307, outline="#34495e", width=3)
        canvas.create_text(
            250, 156, text="Floor Plan Not Found", anchor="center"
        )
        print(f"ERROR: Failed to load floor plan image: {e}")


def show_toast(self, message: str, duration_ms: int = 2500):
    # Use CTkToplevel for better corner radius support
    toast = ctk.CTkToplevel(self)
    toast.overrideredirect(True)
    toast.attributes("-topmost", True)
    pad = 12

    # Create frame with rounded corners
    frame = ctk.CTkFrame(
        toast,
        bg_color="transparent",
        fg_color="#333333",
        corner_radius=5,
    )
    frame.pack(fill="both", expand=True, padx=0, pady=0)

    # Calculate width based on message length
    max_width = 400  # Maximum toast width
    min_width = 200  # Minimum toast width

    label = ctk.CTkLabel(
        frame,
        text=message,
        text_color="white",
        fg_color="transparent",
        wraplength=max_width - 2 * pad,
        justify="left",
        corner_radius=5,
    )
    label.pack(padx=pad, pady=pad)

    # Update to get actual size needed
    toast.update_idletasks()
    req_width = label.winfo_reqwidth() + 2 * pad
    req_height = label.winfo_reqheight() + 2 * pad

    # Clamp width between min and max
    width = max(min_width, min(req_width, max_width))
    height = max(50, req_height)

    # Position at bottom-right corner
    self.update_idletasks()
    x = self.winfo_rootx() + self.winfo_width() - width - 20
    y = self.winfo_rooty() + self.winfo_height() - height - 20
    toast.geometry(f"{width}x{height}+{x}+{y}")

    toast.after(duration_ms, toast.destroy)


def check_line_intersection(p1, p2, p3, p4):
    """
    Check if line segment (p1-p2) intersects with (p3-p4).
    """
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
    if denom == 0:
        return False  # Parallel lines

    ua_num = (x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)
    ub_num = (x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)

    ua = ua_num / denom
    ub = ub_num / denom

    # Intersection must occur within both line segments
    return 0 <= ua <= 1 and 0 <= ub <= 1


def is_sensor_in_rect(sensor, rx1, ry1, rx2, ry2):
    """
    Check if a sensor is inside or intersecting with a rectangle.
    """
    sx, sy = sensor.coordinate_x, sensor.coordinate_y
    min_x, max_x = min(rx1, rx2), max(rx1, rx2)
    min_y, max_y = min(ry1, ry2), max(ry1, ry2)

    # 1. WinDoor Sensor (Point)
    if sensor.get_type() == SensorType.WINDOOR_SENSOR:
        return min_x <= sx <= max_x and min_y <= sy <= max_y

    # 2. Motion Detector (Line Segment)
    elif sensor.get_type() == SensorType.MOTION_DETECTOR_SENSOR:
        sx2 = getattr(sensor, "coordinate_x2", sx)
        sy2 = getattr(sensor, "coordinate_y2", sy)

        # Case A: One of the endpoints is inside the rectangle
        p1_in = min_x <= sx <= max_x and min_y <= sy <= max_y
        p2_in = min_x <= sx2 <= max_x and min_y <= sy2 <= max_y
        if p1_in or p2_in:
            return True

        # Case B: The line passes through the rectangle
        # Check intersection with all 4 sides of the rectangle
        rect_lines = [
            ((min_x, min_y), (max_x, min_y)),  # Top
            ((max_x, min_y), (max_x, max_y)),  # Right
            ((max_x, max_y), (min_x, max_y)),  # Bottom
            ((min_x, max_y), (min_x, min_y)),  # Left
        ]

        sensor_p1 = (sx, sy)
        sensor_p2 = (sx2, sy2)

        for rp1, rp2 in rect_lines:
            if check_line_intersection(sensor_p1, sensor_p2, rp1, rp2):
                return True

        return False

    return False


def find_lowest_empty_id(ids: list[int]) -> int:
    """
    Find the lowest empty ID in a list of IDs (starting from 1).

    Example:
        [2,3,4] -> 1
        [1,2,4] -> 3
        [1,2,3] -> 4
    """
    if not ids:
        return 1

    ids_set = set(ids)
    i = 1
    while i in ids_set:
        i += 1
    return i
