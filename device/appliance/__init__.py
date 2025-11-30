from database.schema.camera import CameraSchema
from device.appliance.camera import SafeHomeCamera


def create_camera_from_schema(camera: CameraSchema) -> SafeHomeCamera:
    cam = SafeHomeCamera()
    cam.id = camera.camera_id
    cam.location = (camera.coordinate_x, camera.coordinate_y)
    cam.pan = camera.pan
    cam.zoom_setting = camera.zoom_setting
    cam._has_password = camera.has_password
    cam.password = camera.password
    cam.enabled = camera.enabled

    if cam.has_password():
        cam.lock()
    else:
        cam.unlock()

    return cam
