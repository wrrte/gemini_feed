from PIL import Image

from database.schema.camera import CameraControlType, CameraValidationResult
from device.appliance.camera import SafeHomeCamera
from manager.storage_manager import StorageManager


class CameraManager:
    def __init__(
        self,
        storage_manager: StorageManager,
    ):
        self.storage_manager = storage_manager
        self.camera_list: list[SafeHomeCamera] = []
        self.num_camera = 0
        self._id_max = 0

        self._load_cameras()

    def _load_cameras(self) -> None:
        """
        Load cameras from DB.
        """
        cameras = self.storage_manager.get_all_cameras()
        for camera in cameras:
            self.camera_list.append(SafeHomeCamera(**camera.model_dump()))

    def get_camera(self, camera_id: int) -> SafeHomeCamera | None:
        for cam in self.camera_list:
            if cam.get_id() == camera_id:
                return cam
        return None

    def add_camera(self, x_coord: int, y_coord: int) -> bool:
        # NOTE: This part is not for implementation in this version.
        camera = SafeHomeCamera(
            camera_id=self._id_max + 1,
            coordinate_x=x_coord,
            coordinate_y=y_coord,
            pan=0,
            zoom_setting=1,
            has_password=False,
            password=None,
            enabled=False,
        )
        self.storage_manager.insert_camera(camera.to_schema())
        self.camera_list.append(camera)
        self._id_max += 1
        return True

    def delete_camera(self, camera_id: int) -> bool:
        # NOTE: This part is not for implementation in this version.
        cam = self.get_camera(camera_id)
        if cam is None:
            return False
        return self.storage_manager.delete_camera(cam.get_id())

    def enable_cameras(self, camera_id_list: list[int]) -> bool:
        """
        Enable cameras in the provided list of camera IDs.
        If any camera ID is invalid, no cameras are enabled.
        """
        staged_cameras: list[SafeHomeCamera] = []

        for camera_id in camera_id_list:
            cam = self.get_camera(camera_id)
            if cam is None:
                return False

            staged_cameras.append(cam)

        for cam in staged_cameras:
            # enable camera
            cam.enable()
            # update camera to DB
            if not self.update_camera(cam.get_id()):
                return False
        return True

    def disable_cameras(self, camera_id_list: list[int]) -> bool:
        """
        Disable cameras in the provided list of camera IDs.
        If any camera ID is invalid, no cameras are disabled.
        """
        staged_cameras: list[SafeHomeCamera] = []

        for camera_id in camera_id_list:
            cam = self.get_camera(camera_id)
            if cam is None:
                return False

            staged_cameras.append(cam)

        for cam in staged_cameras:
            # disable camera
            cam.disable()
            # update camera to DB
            if not self.update_camera(cam.get_id()):
                return False
        return True

    def enable_all_cameras(self) -> bool:
        return self.enable_cameras([cam.get_id() for cam in self.camera_list])

    def disable_all_cameras(self) -> bool:
        return self.disable_cameras([cam.get_id() for cam in self.camera_list])

    def enable_camera(self, camera_id: int) -> bool:
        cam = self.get_camera(camera_id)
        if cam is None:
            return False

        cam.enable()
        # update camera to DB
        if not self.update_camera(cam.get_id()):
            return False
        return True

    def disable_camera(self, camera_id: int) -> bool:
        cam = self.get_camera(camera_id)
        if cam is None:
            return False

        cam.disable()
        # update camera to DB
        if not self.update_camera(cam.get_id()):
            return False
        return True

    def control_single_camera(
        self, camera_id: int, control: CameraControlType
    ) -> bool:
        cam = self.get_camera(camera_id)
        if cam is None:
            return False
        move_success = False

        # move camera
        match control:
            case CameraControlType.PAN_RIGHT:
                move_success = cam.pan_right()
            case CameraControlType.PAN_LEFT:
                move_success = cam.pan_left()
            case CameraControlType.ZOOM_IN:
                move_success = cam.zoom_in()
            case CameraControlType.ZOOM_OUT:
                move_success = cam.zoom_out()
            case _:
                return False

        # update camera to DB
        if not move_success or not self.update_camera(cam.get_id()):
            return False
        return True

    def get_all_thumbnail_views(self) -> list[Image.Image]:
        return [cam.display_view() for cam in self.camera_list]

    def get_single_thumbnail_view(self, camera_id: int) -> Image.Image:
        cam = self.get_camera(camera_id)
        if cam is None:
            return None

        return cam.display_view()

    def get_all_camera_info(self) -> list[dict]:
        return [cam.get_info() for cam in self.camera_list]

    def set_camera_password(self, camera_id: int, password: str) -> None:
        cam = self.get_camera(camera_id)
        if cam is None:
            return

        cam.set_password(password)
        self.update_camera(camera_id)

    def validate_camera_password(
        self, camera_id: int, password: str
    ) -> CameraValidationResult:
        """
        Validates the provided password for the specified camera.
        """
        cam = self.get_camera(camera_id)
        if cam is None:
            return CameraValidationResult.INVALID_ID

        if cam.has_password():
            if password == cam.password:
                return CameraValidationResult.VALID
            else:
                return CameraValidationResult.INCORRECT
        else:
            return CameraValidationResult.NO_PASSWORD

    def delete_camera_password(self, camera_id: int) -> bool:
        cam = self.get_camera(camera_id)
        if cam is None:
            return False

        # remove password
        if cam.has_password():
            cam.set_password(None)

        # update camera to DB
        self.update_camera(camera_id)

        return True

    def update_camera(self, camera_id: int) -> bool:
        """
        Update camera information to database.

        Args:
            camera_id: Camera ID

        Returns:
            True if successful, False otherwise
        """
        cam = self.get_camera(camera_id)
        if cam is None:
            return False
        return self.storage_manager.update_camera(cam.to_schema())
