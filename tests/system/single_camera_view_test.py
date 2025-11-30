import customtkinter as ctk

from core.pages.single_camera_view_page import SingleCameraViewPage
from device.appliance.camera import SafeHomeCamera


def test_camera_single_view_page():
    """
    Manulal test for SingleCameraViewPage. Opens a window showing camera view.
    Panning/Zooming can be tested with arrow keys and +/- keys.
    Close the window to end the test.
    """
    cam = SafeHomeCamera()
    cam.set_id(1)
    cam.enable()

    master = ctk.CTk()
    _ = SingleCameraViewPage(master, camera=cam, initially_hidden=False)
    master.mainloop()


def test_disabled_camera_single_view_page():
    """
    Manulal test for SingleCameraViewPage.
    Opens a window showing camera view of a disabled camera.
    """
    cam = SafeHomeCamera()
    cam.set_id(1)
    cam.disable()

    master = ctk.CTk()
    _ = SingleCameraViewPage(master, camera=cam, initially_hidden=False)
    master.mainloop()
