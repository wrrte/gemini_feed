import os
import tempfile

import pytest
from PIL import Image

from manager.camera_manager import (CameraControlType, CameraManager,
                                    CameraValidationResult)
from manager.storage_manager import StorageManager


@pytest.fixture
def reset_singleton():
    """Reset StorageManager singleton before each test."""
    StorageManager._instance = None
    yield
    StorageManager._instance = None


@pytest.fixture
def storage_manager(reset_singleton):
    """Create a fresh StorageManager for each test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = os.path.join(tmpdir, "test_camera.db")
        manager = StorageManager(db_path=test_db_path, reset_database=True)
        yield manager
        # Cleanup handled by TemporaryDirectory


def test_add_delete_camera(storage_manager):
    cam_manager = CameraManager(storage_manager=storage_manager)

    assert cam_manager.add_camera(10, 20) is True
    assert cam_manager.num_camera == 1
    assert cam_manager.camera_list[0].get_id() == 1
    assert cam_manager.camera_list[0].get_location() == (10, 20)

    assert cam_manager.add_camera(30, 40) is True
    assert cam_manager.num_camera == 2
    assert cam_manager.camera_list[1].get_location() == (30, 40)

    assert cam_manager.delete_camera(1) is True
    assert cam_manager.num_camera == 1
    assert cam_manager.camera_list[0].get_id() == 2
    assert cam_manager.camera_list[0].get_location() == (30, 40)

    assert cam_manager.delete_camera(3) is False
    assert cam_manager.num_camera == 1

    assert cam_manager.add_camera(50, 60) is True
    assert cam_manager.num_camera == 2
    assert cam_manager.camera_list[1].get_id() == 3


def test_enable_disable_cameras(storage_manager):
    cam_manager = CameraManager(storage_manager=storage_manager)
    cam_manager.add_camera(0, 0)  # ID 1
    cam_manager.add_camera(10, 10)  # ID 2
    cam_manager.add_camera(20, 20)  # ID 3

    assert cam_manager.enable_cameras([1, 2]) is True
    assert cam_manager.camera_list[0].is_enabled() is True
    assert cam_manager.camera_list[1].is_enabled() is True
    assert cam_manager.camera_list[2].is_enabled() is False

    assert cam_manager.disable_cameras([2, 3]) is True
    assert cam_manager.camera_list[0].is_enabled() is True
    assert cam_manager.camera_list[1].is_enabled() is False
    assert cam_manager.camera_list[2].is_enabled() is False

    assert cam_manager.enable_cameras([1, 2, 4]) is False
    assert cam_manager.disable_cameras([3, 5]) is False

    cam_manager.enable_all_cameras()
    for cam in cam_manager.camera_list:
        assert cam.is_enabled() is True

    cam_manager.disable_all_cameras()
    for cam in cam_manager.camera_list:
        assert cam.is_enabled() is False

    assert cam_manager.enable_camera(1) is True
    assert cam_manager.camera_list[0].is_enabled() is True
    assert cam_manager.disable_camera(1) is True
    assert cam_manager.camera_list[0].is_enabled() is False


def test_control_single_camera(storage_manager):
    cam_manager = CameraManager(storage_manager=storage_manager)
    cam_manager.add_camera(0, 0)  # ID 1

    assert (
        cam_manager.control_single_camera(2, CameraControlType.PAN_RIGHT)
        is False
    )
    assert cam_manager.control_single_camera(1, 99) is False

    assert (
        cam_manager.control_single_camera(1, CameraControlType.PAN_RIGHT)
        is True
    )
    assert cam_manager.camera_list[0].pan == 1

    assert (
        cam_manager.control_single_camera(1, CameraControlType.PAN_LEFT)
        is True
    )
    assert cam_manager.camera_list[0].pan == 0

    assert (
        cam_manager.control_single_camera(1, CameraControlType.ZOOM_IN) is True
    )
    assert cam_manager.camera_list[0].zoom_setting == 2

    assert (
        cam_manager.control_single_camera(1, CameraControlType.ZOOM_OUT)
        is True
    )
    assert cam_manager.camera_list[0].zoom_setting == 1


def test_display_thumbnail(storage_manager):
    cam_manager = CameraManager(storage_manager=storage_manager)
    cam_manager.add_camera(0, 0)  # ID 1
    cam_manager.add_camera(10, 10)  # ID 2

    thumbnails = cam_manager.display_thumbnail_view()
    assert len(thumbnails) == 2
    for img in thumbnails:
        assert img is not None
        assert isinstance(img, Image.Image)


def test_display_single(storage_manager):
    cam_manager = CameraManager(storage_manager=storage_manager)
    cam_manager.add_camera(0, 0)  # ID 1

    img = cam_manager.display_single_view(1)
    assert img is not None
    assert isinstance(img, Image.Image)

    img_invalid = cam_manager.display_single_view(2)
    assert img_invalid is None


def test_get_all_camera_info(storage_manager):
    cam_manager = CameraManager(storage_manager=storage_manager)
    cam_manager.add_camera(5, 5)  # ID 1
    cam_manager.add_camera(10, 10)  # ID 2

    cam_manager.camera_list[0].set_password("pass1")
    cam_manager.camera_list[1].set_password("pass2")
    cam_manager.camera_list[1].enable()

    info_list = cam_manager.get_all_camera_info()
    assert len(info_list) == 2

    info1 = info_list[0]
    assert info1["id"] == 1
    assert info1["location"] == (5, 5)
    assert info1["zoom"] == 1
    assert info1["pan"] == 0
    assert info1["has_password"] is True
    assert info1["enabled"] is False

    info2 = info_list[1]
    assert info2["id"] == 2
    assert info2["location"] == (10, 10)
    assert info2["zoom"] == 1
    assert info2["pan"] == 0
    assert info2["has_password"] is True
    assert info2["enabled"] is True


def test_camera_password_management(storage_manager):
    cam_manager = CameraManager(storage_manager=storage_manager)
    cam_manager.add_camera(0, 0)  # ID 1

    result = cam_manager.validate_camera_password(1, "SecretPass")
    assert result == CameraValidationResult.NO_PASSWORD

    cam_manager.set_camera_password(1, "SecretPass")
    assert cam_manager.camera_list[0].get_password() == "SecretPass"
    assert cam_manager.camera_list[0].has_password() is True

    result = cam_manager.validate_camera_password(1, "SecretPass")
    assert result == CameraValidationResult.VALID

    result = cam_manager.validate_camera_password(2, "SecretPass")
    assert result == CameraValidationResult.INVALID_ID

    result = cam_manager.validate_camera_password(1, "NoPass")
    assert result == CameraValidationResult.INCORRECT

    assert cam_manager.delete_camera_password(2) is False
    assert cam_manager.delete_camera_password(1) is True
    assert cam_manager.camera_list[0].get_password() is None
    assert cam_manager.camera_list[0].has_password() is False
