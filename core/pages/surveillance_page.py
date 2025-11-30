from typing import Callable, Optional

import customtkinter as ctk

from core.pages.interface_page import InterfacePage
from core.pages.utils import draw_floor_plan, show_toast
from manager.camera_manager import CameraManager, CameraValidationResult


class SurveillancePage(InterfacePage):
    def __init__(
        self,
        master,
        page_id,
        camera_manager: CameraManager,
        show_multi_camera: Optional[Callable] = None,
        show_single_camera: Optional[Callable[[int], None]] = None,
        **kwargs,
    ):
        super().__init__(master, page_id, **kwargs)
        self.camera_manager = camera_manager
        self.show_multi_camera = show_multi_camera
        self.show_single_camera = show_single_camera
        self.draw_page()

    def draw_page(self):
        # Grid configuration (left: flexible, right: fixed 570px)
        self.grid_columnconfigure(0, weight=1)  # Left takes remaining space
        self.grid_columnconfigure(
            1, weight=0, minsize=600)  # Right fixed 570px
        self.grid_rowconfigure(0, weight=1)

        # ===== Left Panel (Controls + Status) =====
        self.left_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.left_panel.grid_rowconfigure(0, weight=0)
        self.left_panel.grid_rowconfigure(1, weight=1)
        self.left_panel.grid_columnconfigure(0, weight=1)

        # 1. Control Section
        self.control_frame = ctk.CTkFrame(self.left_panel, corner_radius=10)
        self.control_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        ctk.CTkLabel(
            self.control_frame,
            text="Camera Controls",
            font=("Arial", 16, "bold"),
        ).grid(
            row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w"
        )

        # Configure grid for buttons (2 columns)
        self.control_frame.grid_columnconfigure(0, weight=1)
        self.control_frame.grid_columnconfigure(1, weight=1)

        # Row 1: Enable | Disable
        self.enable_btn = ctk.CTkButton(
            self.control_frame,
            text="Enable Camera",
            command=self.enable_camera,
            height=35,
            state="disabled",
        )
        self.enable_btn.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        self.disable_btn = ctk.CTkButton(
            self.control_frame,
            text="Disable Camera",
            command=self.disable_camera,
            height=35,
            state="disabled",
            fg_color="#c0392b",
            hover_color="#a83224",
        )
        self.disable_btn.grid(row=1, column=1, padx=10, pady=5, sticky="nsew")

        # Row 2: View | Set Password
        self.view_btn = ctk.CTkButton(
            self.control_frame,
            text="View Camera",
            command=self.view_cam,
            state="disabled",
            height=35,
        )
        self.view_btn.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")

        self.setpwd_btn = ctk.CTkButton(
            self.control_frame,
            text="Configure Password",
            command=self.set_pwd,
            state="disabled",
            height=35,
        )
        self.setpwd_btn.grid(row=2, column=1, padx=10, pady=5, sticky="nsew")

        # Row 3: Display all thumbnails (single button spanning 2 columns)
        self.multiview_btn = ctk.CTkButton(
            self.control_frame,
            text="Display All Cameras (Thumbnail View)",
            command=lambda: self.show_multi_camera(),
            height=35,
        )
        self.multiview_btn.grid(
            row=3, column=0, columnspan=2, padx=10, pady=(10, 8), sticky="nsew"
        )
        # 2. Status Section
        self.status_frame = ctk.CTkFrame(self.left_panel, corner_radius=10)
        self.status_frame.grid(row=1, column=0, sticky="nsew")

        ctk.CTkLabel(
            self.status_frame, text="Camera Status", font=("Arial", 16, "bold")
        ).pack(pady=10, padx=10, anchor="w")

        self.status_list = ctk.CTkScrollableFrame(
            self.status_frame, fg_color="transparent"
        )
        self.status_list.pack(fill="both", expand=True, padx=5, pady=5)

        # Mock Status
        self._display_camera_status()

        # ===== Right Panel (Floor Plan) =====
        self.right_panel = ctk.CTkFrame(self, corner_radius=10)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(
            self.right_panel,
            text="Floor Plan View",
            font=("Arial", 16, "bold"),
        ).pack(pady=10)

        # Canvas
        self.canvas = ctk.CTkCanvas(
            self.right_panel,
            bg="#ecf0f1",
            highlightthickness=0,
            width=500,
            height=312,
        )
        # Center the canvas with padding
        self.canvas.pack(padx=10, pady=10)

        # After canvas is ready, draw the floor plan and cameras
        self.canvas.bind("<Configure>", self._on_canvas_ready)

    def _on_canvas_ready(self, event=None):
        # Debounce (prevent rapid consecutive calls)
        if getattr(self, "_fp_job", None):
            self.canvas.after_cancel(self._fp_job)

        def _render():
            self._draw_floor_plan()
            self._draw_cameras()

        self._fp_job = self.canvas.after(50, _render)

    def _display_camera_status(self):
        camera_info_list = self.camera_manager.get_all_camera_info()
        self._status_items = []
        self._status_lbls = []
        self._locked_lbls = []

        for idx, cam_info in enumerate(camera_info_list):
            item_frame = ctk.CTkFrame(self.status_list, height=40)
            item_frame.pack(fill="x", pady=2)
            item_frame.bind("<Button-1>", self._status_item_click_handler)
            item_frame._cam_index = idx

            name_lbl = ctk.CTkLabel(
                item_frame,
                text=f"Camera {cam_info['camera_id']}",
                font=("Arial", 12),
            )
            name_lbl.pack(side="left", padx=10)
            name_lbl.bind("<Button-1>", self._status_item_click_handler)

            enabled = cam_info["enabled"]
            enabled_text = "Enabled" if enabled else "Disabled"
            color = "#27ae60" if enabled else "#000000"
            state_lbl = ctk.CTkLabel(
                item_frame,
                text=enabled_text,
                font=("Arial", 12, "bold"),
                text_color=color,
            )
            state_lbl.pack(side="right", padx=10)
            state_lbl.bind("<Button-1>", self._status_item_click_handler)
            state_lbl._cam_index = idx

            # Password protection status label (always created, conditionally
            # shown)
            locked_lbl = ctk.CTkLabel(
                item_frame,
                text="Locked",
                font=("Arial", 12, "bold"),
                text_color="#e74c3c",
            )
            locked_lbl.bind("<Button-1>", self._status_item_click_handler)
            locked_lbl._cam_index = idx

            # Show only when has_password is True
            has_password = cam_info.get("has_password", False)
            if has_password:
                locked_lbl.pack(side="right", padx=10)

            self._status_items.append(item_frame)
            self._status_lbls.append(state_lbl)
            self._locked_lbls.append(locked_lbl)

    def _draw_floor_plan(self):
        # Use original image size (500x312) - no scaling needed
        draw_floor_plan(self.canvas)

    def _draw_cameras(self):
        camera_info_list = self.camera_manager.get_all_camera_info()
        for cam_info in camera_info_list:
            x, y = cam_info["coordinate_x"], cam_info["coordinate_y"]
            self.canvas.create_oval(
                x - 5, y - 5, x + 5, y + 5, fill="blue", outline=""
            )
            text = f"Cam {cam_info['camera_id']}"
            self.canvas.create_text(
                x - 15,
                y,
                text=text,
                anchor="e",
                font=("Arial", 10),
                fill="blue",
            )

    # Handlers
    def enable_camera(self):
        self.camera_manager.enable_camera(self._selected_cam_index + 1)
        self._update_controls_and_status()

    def disable_camera(self):
        self.camera_manager.disable_camera(self._selected_cam_index + 1)
        self._update_controls_and_status()

    def _prompt_password(self, title, text) -> Optional[str]:
        """
        Prompt user for a password input.
        Returns the entered password, or None if cancelled.
        """
        pwd_box = ctk.CTkInputDialog(title=title, text=text)
        pwd = pwd_box.get_input()
        if pwd == "":
            return None
        return pwd

    def show_toast(self, message: str, duration_ms: int = 2500):
        toast = ctk.CTkToplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)

        frame = ctk.CTkFrame(toast, fg_color="#333333", corner_radius=0)
        frame.pack(fill="both", expand=True)

        lbl = ctk.CTkLabel(
            frame,
            text=message,
            text_color="#ffffff",
            font=ctk.CTkFont(size=13, weight="bold"),
            justify="left",
        )
        lbl.pack(padx=14, pady=10)

        # Calculate sizes
        toast.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width() - 350
        y = self.winfo_rooty() + self.winfo_height() - 100
        toast.geometry(f"260x50+{x}+{y}")

        # Auto-destroy
        toast.after(duration_ms, toast.destroy)

    def view_cam(self):
        camera = self.camera_manager.camera_list[self._selected_cam_index]

        if camera.is_locked() is True:
            pwd = self._prompt_password("Camera Password", "Enter password:")
            if pwd is None:
                return

            valid = self.camera_manager.validate_camera_password(
                camera.get_id(), pwd
            )

            match valid:
                case CameraValidationResult.VALID:
                    camera.unlock()
                case CameraValidationResult.INCORRECT:
                    show_toast(self.master, "Incorrect password")
                    return
                case _:
                    print("Unexpected validation result")
                    return

        if self.show_single_camera:
            self.show_single_camera(camera.get_id())

    def _prompt_new_password(
        self, title: str = "Set Camera Password"
    ) -> Optional[str]:
        """Open a modal dialog with two password fields and validation."""
        dlg = ctk.CTkToplevel(self)
        dlg.title(title)
        dlg.geometry("340x250")
        dlg.resizable(False, False)
        dlg.grab_set()

        ctk.CTkLabel(dlg, text="Enter new password:").pack(
            padx=14, pady=(12, 4), anchor="w"
        )
        entry1 = ctk.CTkEntry(dlg, show="*")
        entry1.pack(padx=14, fill="x")

        ctk.CTkLabel(dlg, text="Confirm password:").pack(
            padx=14, pady=(10, 4), anchor="w"
        )
        entry2 = ctk.CTkEntry(dlg, show="*")
        entry2.pack(padx=14, fill="x")

        error_lbl = ctk.CTkLabel(
            dlg, text="", text_color="#c0392b", wraplength=300
        )
        error_lbl.pack(padx=14, pady=(8, 4), anchor="w")

        self._new_password = None

        def validate_and_close():
            p1 = entry1.get().strip()
            p2 = entry2.get().strip()
            if not p1 or len(p1) < 4:
                error_lbl.configure(
                    text="The password must be longer than 4 characters"
                )
                return
            if p1 != p2:
                error_lbl.configure(text="Passwords do not match")
                return
            self._new_password = p1
            try:
                dlg.grab_release()
            except Exception:
                pass
            dlg.destroy()

        def delete():
            dlg.destroy()
            self._new_password = "DEL"

        def cancel():
            try:
                dlg.grab_release()
            except Exception:
                pass
            dlg.destroy()

        btn_frame = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_frame.pack(pady=(6, 10))
        ok_btn = ctk.CTkButton(
            btn_frame, text="OK", width=100, command=validate_and_close
        )
        ok_btn.pack(side="left", padx=8)
        delete_btn = ctk.CTkButton(
            btn_frame, text="Delete password", width=120, command=delete
        )
        delete_btn.pack(side="left", padx=8)
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=100,
            fg_color="#7f8c8d",
            hover_color="#707b7c",
            command=cancel,
        )
        cancel_btn.pack(side="left", padx=8)

        entry1.focus_set()
        dlg.wait_window(dlg)
        return self._new_password

    def set_pwd(self):
        camera = self.camera_manager.camera_list[self._selected_cam_index]

        if camera.is_locked() is True:
            pwd = self._prompt_password(
                "Camera Password", "Enter current password:"
            )
            if pwd is None:
                return

            valid = self.camera_manager.validate_camera_password(
                camera.get_id(), pwd
            )

            match valid:
                case CameraValidationResult.VALID:
                    pass
                case CameraValidationResult.INCORRECT:
                    show_toast(self.master, "Incorrect password")
                    return
                case _:
                    print("Unexpected validation result")
                    return

        new_pwd = self._prompt_new_password("Set Camera Password")
        if new_pwd is None:
            return
        elif new_pwd == "DEL":
            camera.set_password(None)
            show_toast(self.master, "Password deleted")
        else:
            camera.set_password(new_pwd)
            show_toast(self.master, "Password updated")

        self.camera_manager.set_camera_password(
            camera.get_id(), camera.get_password()
        )

        # Update UI (reflect lock status)
        self._update_controls_and_status()

    def _status_item_click_handler(self, event):
        """
        Handle click on a status row.
        finds camera index and updates controls.
        """
        # Click can be triggered from temporary child Ctk object
        w = event.widget
        while w is not None and not hasattr(w, "_cam_index"):
            w = getattr(w, "master", None)

        idx = getattr(w, "_cam_index", None)
        if idx is None:
            return

        # Visual feedback: highlight selected row
        for i, row in enumerate(self._status_items):
            row.configure(fg_color="#c9c9c9" if i == idx else "transparent")

        # Enable control buttons for this selection
        self._selected_cam_index = idx
        self._update_controls_and_status()

    def _update_controls_and_status(self):
        cam_infos = self.camera_manager.get_all_camera_info()
        cam_info = cam_infos[self._selected_cam_index]
        index = self._selected_cam_index

        if cam_info["enabled"]:
            self.enable_btn.configure(state="disabled")
            self.disable_btn.configure(state="normal")
            self.view_btn.configure(state="normal")
            self._status_lbls[index].configure(
                text="Enabled", text_color="#27ae60"
            )
        else:
            self.enable_btn.configure(state="normal")
            self.disable_btn.configure(state="disabled")
            self.view_btn.configure(state="disabled")
            self._status_lbls[index].configure(
                text="Disabled", text_color="#000000"
            )

        if cam_info["locked"]:
            self._locked_lbls[index].configure(
                text="Locked", text_color="#000000"
            )
        else:
            self._locked_lbls[index].configure(
                text="", text_color="#000000"
            )

        self.setpwd_btn.configure(state="normal")

        # Update lock status (dynamically show/hide)
        has_password = cam_info.get("has_password", False)
        locked_lbl = self._locked_lbls[self._selected_cam_index]
        if has_password:
            locked_lbl.pack(side="right", padx=10)
        else:
            locked_lbl.pack_forget()

    def destroy(self):
        cam_list = self.camera_manager.camera_list
        for cam in cam_list:
            self.camera_manager.update_camera(cam.get_id())
        return super().destroy()
