from typing import Optional

import customtkinter as ctk
from PIL import Image

from core.pages.interface_page import InterfaceWindow
from database.schema.camera import CameraControlType
from manager.camera_manager import CameraManager


class SingleCameraViewPage(InterfaceWindow):
    """
    Single camera viewer window with controls.
    Displays real-time camera feed with pan and zoom controls.
    """

    DISPLAY_SIZE = (500, 500)

    def __init__(
        self,
        master,
        page_id: str = "SingleCameraView",
        camera_manager: Optional[CameraManager] = None,
        camera_id: Optional[int] = None,
        initially_hidden: bool = True,
        **kwargs,
    ):
        """
        Initialize Single Camera View Page.

        Args:
            master: Parent widget
            page_id: Page identifier
            camera_manager: CameraManager instance
            camera_id: Camera ID to display
            initially_hidden: Whether to initially hide the page
        """

        super().__init__(
            master=master,
            page_id=page_id,
            title="SafeHome Camera Viewer",
            initially_hidden=initially_hidden,
            **kwargs,
        )

        self.geometry("550x700")
        self.resizable(False, False)

        # instances
        self.camera_manager = camera_manager
        self.camera_id = camera_id
        self.update_count = 0
        self._buttons: list[ctk.CTkButton] = []
        self._img_ref = None
        self._update_interval_ms = 100
        self._is_running = True
        self._after_id = None

        # Draw the page
        self.draw_page()

        # Start camera updates if camera is provided
        if self.camera_id:
            self.update_view()

    def draw_page(self):
        """Draw the camera viewer UI."""
        # Header
        header = ctk.CTkLabel(
            self,
            text="🎥 SafeHome Camera Viewer",
            font=("Arial", 20, "bold"),
            text_color="#1f538d",
        )
        header.pack(pady=5, padx=10, fill="x")

        # Camera canvas frame
        canvas_frame = ctk.CTkFrame(
            self,
            width=self.DISPLAY_SIZE[0],
            height=self.DISPLAY_SIZE[1],
            fg_color="#2b2b2b",
            border_width=1,
            border_color="gray",
        )
        canvas_frame.pack(pady=0, padx=0)
        canvas_frame.pack_propagate(False)

        # Use CTklabel for image display
        self.image_label = ctk.CTkLabel(
            canvas_frame,
            text="",
            width=self.DISPLAY_SIZE[0],
            height=self.DISPLAY_SIZE[1],
        )
        self.image_label.pack(padx=0, pady=0)

        initial_img = Image.new("RGB", self.DISPLAY_SIZE, "black")
        ctk_img = ctk.CTkImage(initial_img, None, size=self.DISPLAY_SIZE)
        self.image_label.configure(image=ctk_img)
        self._img_ref = ctk_img

        # Status display
        self.status_label = ctk.CTkLabel(
            self,
            text="Camera Status: Ready",
            font=("Courier", 12, "bold"),
            fg_color="#fff3cd",
            text_color="#004085",
            corner_radius=5,
            height=25,
        )
        self.status_label.pack(pady=10, padx=20, fill="x")

        # Control frame
        control_frame = ctk.CTkFrame(
            self, fg_color="#e9ecef", border_width=2, corner_radius=5
        )
        control_frame.pack(pady=5, padx=20, fill="x")

        # Control title
        control_title = ctk.CTkLabel(
            control_frame,
            text="Camera Controls",
            height=25,
            font=("Arial", 12, "bold"),
            text_color="#2c3e50",
        )
        control_title.pack(pady=3)

        # Button container
        btn_container = ctk.CTkFrame(control_frame, fg_color="transparent")
        btn_container.pack(pady=5)

        # Pan controls
        pan_frame = ctk.CTkFrame(btn_container, fg_color="transparent")
        pan_frame.grid(row=0, column=0, padx=15, pady=0)

        ctk.CTkLabel(
            pan_frame,
            text="Pan",
            height=15,
            font=("Arial", 12, "bold"),
            text_color="#34495e",
        ).pack(pady=0)

        pan_btn_frame = ctk.CTkFrame(pan_frame, fg_color="transparent")
        pan_btn_frame.pack()

        lpan_btn = ctk.CTkButton(
            pan_btn_frame,
            text="◀◀ Left",
            command=self.pan_left,
            width=100,
            height=30,
            fg_color="#3498db",
            hover_color="#2980b9",
            font=("Arial", 11, "bold"),
        )
        lpan_btn.pack(side="left", padx=5, pady=5)

        rpan_btn = ctk.CTkButton(
            pan_btn_frame,
            text="Right ▶▶",
            command=self.pan_right,
            width=100,
            height=30,
            fg_color="#3498db",
            hover_color="#2980b9",
            font=("Arial", 11, "bold"),
        )
        rpan_btn.pack(side="left", padx=5, pady=5)

        # Zoom controls
        zoom_frame = ctk.CTkFrame(btn_container, fg_color="transparent")
        zoom_frame.grid(row=0, column=1, padx=15, pady=0)

        ctk.CTkLabel(
            zoom_frame,
            text="Zoom",
            height=15,
            font=("Arial", 12, "bold"),
            text_color="#34495e",
        ).pack(pady=0)

        zoom_btn_frame = ctk.CTkFrame(zoom_frame, fg_color="transparent")
        zoom_btn_frame.pack()

        zin_button = ctk.CTkButton(
            zoom_btn_frame,
            text="🔍+ In",
            command=self.zoom_in,
            width=100,
            height=30,
            fg_color="#27ae60",
            hover_color="#229954",
            font=("Arial", 11, "bold"),
        )
        zin_button.pack(side="left", padx=5, pady=5)

        zout_button = ctk.CTkButton(
            zoom_btn_frame,
            text="🔍- Out",
            command=self.zoom_out,
            width=100,
            height=30,
            fg_color="#27ae60",
            hover_color="#229954",
            font=("Arial", 11, "bold"),
        )
        zout_button.pack(side="left", padx=5, pady=5)

        self._buttons = [lpan_btn, rpan_btn, zin_button, zout_button]

    def update_view(self):
        """Update camera view and status."""
        self.update_count += 1
        camera = self.camera_manager.get_camera(self.camera_id)

        if camera is None:
            self.destroy()
            return

        if camera.is_locked():
            self.destroy()
            return

        try:
            img = camera.display_view()
            if img is None:
                return

            # Convert to PhotoImage and update canvas
            if img.size != self.DISPLAY_SIZE:
                img = img.resize(self.DISPLAY_SIZE, Image.LANCZOS)
            ctk_img = ctk.CTkImage(img, None, size=self.DISPLAY_SIZE)
            self.image_label.configure(image=ctk_img)
            self._img_ref = ctk_img

        except Exception as e:
            if self.update_count <= 3:
                print(f"ERROR in update_view: {e}")

        # Update status
        try:
            camera_id = camera.get_id()
            zoom = camera.zoom_setting
            pan = camera.pan
            enabled = camera.enabled

            status = f"Camera ID: {camera_id} | "
            status += f"Enabled: {enabled} | "
            status += f"Zoom: {zoom}x | "
            if pan > 0:
                status += f"Pan: Right {pan}"
            elif pan == 0:
                status += "Pan: Center"
            else:
                status += f"Pan: Left {abs(pan)}"

            self.status_label.configure(text=status)
        except Exception as e:
            if self.update_count <= 3:
                print(f"ERROR updating status: {e}")

        # Disable buttons if camera is disabled
        if not camera.is_enabled():
            for btn in self._buttons:
                btn.configure(state="disabled")

        # Schedule next update (100ms = 10 FPS)
        if self._is_running:
            self._after_id = self.after(
                self._update_interval_ms, self.update_view
            )

    def pan_left(self):
        """Pan camera to the left."""
        camera = self.camera_manager.get_camera(self.camera_id)
        if camera and camera.is_enabled():
            self.camera_manager.control_single_camera(
                camera.get_id(), CameraControlType.PAN_LEFT
            )

    def pan_right(self):
        """Pan camera to the right."""
        camera = self.camera_manager.get_camera(self.camera_id)
        if camera and camera.is_enabled():
            self.camera_manager.control_single_camera(
                camera.get_id(), CameraControlType.PAN_RIGHT
            )

    def zoom_in(self):
        """Zoom in the camera."""
        camera = self.camera_manager.get_camera(self.camera_id)
        if camera and camera.is_enabled():
            self.camera_manager.control_single_camera(
                camera.get_id(), CameraControlType.ZOOM_IN
            )

    def zoom_out(self):
        """Zoom out the camera."""
        camera = self.camera_manager.get_camera(self.camera_id)
        if camera and camera.is_enabled():
            self.camera_manager.control_single_camera(
                camera.get_id(), CameraControlType.ZOOM_OUT
            )

    def destroy(self):
        """
        Cleanup when window is destroyed.
        If the camera has password, lock it.
        """
        camera = self.camera_manager.get_camera(self.camera_id)
        if camera and camera.has_password():
            camera.lock()

        self._is_running = False
        if self._after_id is not None:
            self.after_cancel(self._after_id)

        self._buttons = []
        super().destroy()
