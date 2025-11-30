from typing import Callable, List, Optional

import customtkinter as ctk
from PIL import Image

from core.pages.interface_page import InterfaceWindow
from manager.camera_manager import CameraManager, CameraValidationResult


class _ClickableLabel(ctk.CTkLabel):
    def __init__(self, master, index: int, click_handler, **kwargs):
        super().__init__(master, **kwargs)
        self.index = index
        self.click_handler = click_handler
        self.bind("<Button-1>", self._on_click)

    def _on_click(self, _event):
        self.click_handler(self.index)


class MultiCameraViewPage(InterfaceWindow):
    """
    2x2 multi-camera view using customtkinter.
    Empty slots appear as black boxes.
    Clicking a slot opens the single camera view page for that camera.
    """

    CELLS_IN_ROW = 2

    def __init__(
        self,
        master,
        camera_manager: CameraManager,
        page_id: str = "MultiCameraView",
        initially_hidden: bool = True,
        show_single_camera: Optional[Callable[[int], None]] = None,
        **kwargs,
    ):
        super().__init__(
            master=master,
            page_id=page_id,
            title="SafeHome Camera Grid View",
            initially_hidden=initially_hidden,
            **kwargs,
        )

        self.camera_manager = camera_manager
        self.show_single_camera = show_single_camera
        self.title("Multi Camera View")
        self.geometry("700x700")
        self.resizable(True, False)

        self._labels: List[_ClickableLabel] = []
        self._photo_refs: List[Optional[ctk.CTkImage]] = []
        self._update_interval_ms = 200
        self._is_running = True
        self._after_id = None
        self._grid_width = 690  # fixed container width
        self._grid_height = 690  # fixed container height

        self.draw_page()
        if self.camera_manager:
            # Defer initial refresh so widgets have real size
            self._after_id = self.after(100, self.refresh_frames)

    def draw_page(self):
        # use fixed-size container; disable geometry propagation
        container = ctk.CTkFrame(
            self, width=self._grid_width, height=self._grid_height
        )
        container.pack(padx=8, pady=8)  # no fill/expand => stays fixed
        container.pack_propagate(False)
        self._container = container

        for i in range(4):
            if i >= len(self.camera_manager.camera_list):
                text = "No Camera"
            else:
                text = f"Camera {i + 1}"

            lbl = _ClickableLabel(
                container,
                index=i,
                click_handler=self.handle_slot_click,
                text=text,
                fg_color="#000000",
                text_color="#999999",
                font=ctk.CTkFont(size=14),
                width=self._grid_width // self.CELLS_IN_ROW,
                height=self._grid_height // self.CELLS_IN_ROW,
            )
            lbl.grid(
                row=i // self.CELLS_IN_ROW,
                column=i % self.CELLS_IN_ROW,
                sticky="nsew",
                padx=5,
                pady=5,
            )
            self._labels.append(lbl)
            self._photo_refs.append(None)

        # Configure grid weights for resizing
        for r in range(2):
            container.grid_rowconfigure(r, weight=1)
        for c in range(2):
            container.grid_columnconfigure(c, weight=1)
        # prevent grid shrinking to image sizes
        container.grid_propagate(False)

    def refresh_frames(self):
        cams = self.camera_manager.camera_list
        cell_w = self._grid_width // self.CELLS_IN_ROW - 6
        cell_h = self._grid_height // self.CELLS_IN_ROW - 6

        for i, lbl in enumerate(self._labels):
            if i >= len(cams):
                continue
            cam = cams[i]

            frame = cam.display_view()
            if frame is None:
                continue

            if frame.size != (cell_w, cell_h):
                frame = frame.resize((cell_w, cell_h), Image.LANCZOS)

            ctk_img = ctk.CTkImage(frame, None, size=(cell_w, cell_h))

            if not cam.is_enabled():
                lbl.configure(image=ctk_img, text="Disabled")
            elif cam.is_locked():
                lbl.configure(image=ctk_img, text="Locked")
            else:
                lbl.configure(image=ctk_img, text="")

            self._photo_refs[i] = ctk_img  # keep reference

        if self._is_running:
            self._after_id = self.after(
                self._update_interval_ms, self.refresh_frames
            )

    def handle_slot_click(self, index: int):
        """
        Open single camera view for clicked slot if camera exists.
        """
        if index >= len(self.camera_manager.camera_list):
            return
        camera = self.camera_manager.camera_list[index]

        if camera.is_enabled() is False:
            return

        if camera.is_locked() is True:
            pwd = self._prompt_password()
            if pwd is None:
                return

            valid = self.camera_manager.validate_camera_password(
                camera.get_id(), pwd
            )

            match valid:
                case CameraValidationResult.VALID:
                    camera.unlock()
                case CameraValidationResult.INCORRECT:
                    self.show_toast("Incorrect password")
                    camera.lock()
                    return
                case _:
                    print("Unexpected validation result")
                    return

        if self.show_single_camera:
            self.show_single_camera(camera.get_id())

    def _prompt_password(self) -> Optional[str]:
        """
        Prompt user for camera password.
        Returns the entered password, or None if cancelled.
        """
        pwd_box = ctk.CTkInputDialog(
            title="Camera Password", text="Enter password:"
        )
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

    def destroy(self):
        for cam in self.camera_manager.camera_list:
            if cam.has_password():
                cam.lock()

        self._is_running = False
        if self._after_id is not None:
            self.after_cancel(self._after_id)

        self._labels = []
        self._photo_refs = None
        super().destroy()
