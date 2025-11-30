import customtkinter as ctk

from core.pages.multi_camera_view_page import MultiCameraViewPage
from manager.camera_manager import CameraManager


def test_camera_multi_view_page():
    """
    Manulal test for SingleCameraViewPage. Opens a window showing camera view.
    Panning/Zooming can be tested with arrow keys and +/- keys.
    Close the window to end the test.
    """
    cam_manager = CameraManager()
    cam_manager.add_camera(10, 20)  # ID 1
    cam_manager.add_camera(30, 40)  # ID 2
    cam_manager.add_camera(50, 60)  # ID 3
    cam_manager.add_camera(70, 80)  # ID 4

    cam_manager.enable_all_cameras()
    cam_manager.disable_camera(2)
    cam_manager.set_camera_password(3, "password")

    master = ctk.CTk()
    _ = MultiCameraViewPage(master, cam_manager, initially_hidden=False)
    master.mainloop()
