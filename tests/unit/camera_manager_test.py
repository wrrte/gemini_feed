import pytest
from unittest.mock import Mock, patch
from manager.camera_manager import CameraManager
from manager.storage_manager import StorageManager
from database.schema.camera import CameraSchema, CameraControlType, CameraValidationResult

@pytest.fixture
def mock_storage_manager():
    return Mock(spec=StorageManager)

@pytest.fixture
def mock_safe_home_camera_class():
    with patch("manager.camera_manager.SafeHomeCamera") as mock_class:
        yield mock_class

@pytest.fixture
def camera_manager(mock_storage_manager, mock_safe_home_camera_class):
    # Setup initial mock data for _load_cameras
    mock_camera_schema = Mock(spec=CameraSchema)
    mock_camera_schema.model_dump.return_value = {"camera_id": 1, "enabled": True}
    mock_storage_manager.get_all_cameras.return_value = [mock_camera_schema]
    
    # Setup the mock instance returned by SafeHomeCamera()
    mock_instance = mock_safe_home_camera_class.return_value
    mock_instance.get_id.return_value = 1
    # Allow mocking methods on the instance
    mock_instance.pan_right.return_value = True
    mock_instance.pan_left.return_value = True
    mock_instance.zoom_in.return_value = True
    mock_instance.zoom_out.return_value = True
    
    manager = CameraManager(storage_manager=mock_storage_manager)
    return manager

@pytest.mark.parametrize("camera_id, expected_found", [
    (1, True),
    (999, False)
])
def test_get_camera(camera_manager, camera_id, expected_found):
    cam = camera_manager.get_camera(camera_id)
    if expected_found:
        assert cam is not None
        assert cam.get_id() == camera_id
    else:
        assert cam is None

def test_add_camera(camera_manager, mock_storage_manager):
    result = camera_manager.add_camera(10, 20)
    assert result is True
    assert camera_manager._id_max == 1
    assert len(camera_manager.camera_list) == 2
    mock_storage_manager.insert_camera.assert_called_once()

@pytest.mark.parametrize("camera_id, delete_success, expected_result", [
    (1, True, True),
    (1, False, False),
    (999, True, False) # Camera not found
])
def test_delete_camera(camera_manager, mock_storage_manager, camera_id, delete_success, expected_result):
    mock_storage_manager.delete_camera.return_value = delete_success
    result = camera_manager.delete_camera(camera_id)
    assert result is expected_result
    if camera_id == 1:
        mock_storage_manager.delete_camera.assert_called_with(1)
    else:
        mock_storage_manager.delete_camera.assert_not_called()

@pytest.mark.parametrize("ids, db_success, expected_result", [
    ([1], True, True),
    ([1, 999], True, False), # One invalid ID
    ([1], False, False)      # DB update fails
])
def test_enable_cameras(camera_manager, mock_storage_manager, ids, db_success, expected_result):
    mock_storage_manager.update_camera.return_value = db_success
    result = camera_manager.enable_cameras(ids)
    assert result is expected_result
    
    if expected_result:
        cam = camera_manager.get_camera(1)
        cam.enable.assert_called()

@pytest.mark.parametrize("ids, db_success, expected_result", [
    ([1], True, True),
    ([1, 999], True, False),
    ([1], False, False)
])
def test_disable_cameras(camera_manager, mock_storage_manager, ids, db_success, expected_result):
    mock_storage_manager.update_camera.return_value = db_success
    result = camera_manager.disable_cameras(ids)
    assert result is expected_result

    if expected_result:
        cam = camera_manager.get_camera(1)
        cam.disable.assert_called()

@pytest.mark.parametrize("action, expected_method", [
    ("enable", "enable"),
    ("disable", "disable")
])
def test_toggle_all_cameras(camera_manager, mock_storage_manager, action, expected_method):
    mock_storage_manager.update_camera.return_value = True
    
    if action == "enable":
        assert camera_manager.enable_all_cameras() is True
    else:
        assert camera_manager.disable_all_cameras() is True
        
    cam = camera_manager.get_camera(1)
    getattr(cam, expected_method).assert_called()

@pytest.mark.parametrize("camera_id, action, db_success, expected_result", [
    (1, "enable", True, True),
    (1, "enable", False, False),
    (999, "enable", True, False),
    (1, "disable", True, True),
    (1, "disable", False, False),
    (999, "disable", True, False),
])
def test_toggle_single_camera(camera_manager, mock_storage_manager, camera_id, action, db_success, expected_result):
    mock_storage_manager.update_camera.return_value = db_success
    
    if action == "enable":
        assert camera_manager.enable_camera(camera_id) is expected_result
    else:
        assert camera_manager.disable_camera(camera_id) is expected_result

@pytest.mark.parametrize("control_type, move_success, db_success, expected_result", [
    (CameraControlType.PAN_RIGHT, True, True, True),
    (CameraControlType.PAN_LEFT, True, True, True),
    (CameraControlType.ZOOM_IN, True, True, True),
    (CameraControlType.ZOOM_OUT, True, True, True),
    (CameraControlType.PAN_RIGHT, False, True, False), # Move fails
    (CameraControlType.PAN_RIGHT, True, False, False), # DB fails
    ("INVALID_CONTROL", True, True, False)             # Invalid control enum
])
def test_control_single_camera(camera_manager, mock_storage_manager, control_type, move_success, db_success, expected_result):
    cam = camera_manager.get_camera(1)
    
    # Configure mock behavior
    cam.pan_right.return_value = move_success
    cam.pan_left.return_value = move_success
    cam.zoom_in.return_value = move_success
    cam.zoom_out.return_value = move_success
    
    mock_storage_manager.update_camera.return_value = db_success
    
    result = camera_manager.control_single_camera(1, control_type)
    assert result is expected_result

def test_control_single_camera_invalid_id(camera_manager):
    assert camera_manager.control_single_camera(999, CameraControlType.PAN_RIGHT) is False

def test_thumbnail_methods(camera_manager):
    cam = camera_manager.get_camera(1)
    
    # Test get all
    camera_manager.get_all_thumbnail_views()
    cam.display_view.assert_called()
    
    # Test get single
    camera_manager.get_single_thumbnail_view(1)
    assert cam.display_view.call_count == 2
    
    # Test get single invalid
    assert camera_manager.get_single_thumbnail_view(999) is None

def test_get_all_camera_info(camera_manager):
    camera_manager.get_all_camera_info()
    camera_manager.get_camera(1).get_info.assert_called_once()

@pytest.mark.parametrize("camera_id, should_update", [
    (1, True),
    (999, False)
])
def test_set_camera_password(camera_manager, mock_storage_manager, camera_id, should_update):
    cam = camera_manager.get_camera(1)
    camera_manager.set_camera_password(camera_id, "new_pass")
    
    if should_update:
        cam.set_password.assert_called_with("new_pass")
        mock_storage_manager.update_camera.assert_called_with(camera_id)
    else:
        cam.set_password.assert_not_called()
        mock_storage_manager.update_camera.assert_not_called()

@pytest.mark.parametrize("camera_id, has_pwd, correct_pwd, input_pwd, expected", [
    (1, True, "1234", "1234", CameraValidationResult.VALID),
    (1, True, "1234", "wrong", CameraValidationResult.INCORRECT),
    (1, False, None, "any", CameraValidationResult.NO_PASSWORD),
    (999, False, None, "any", CameraValidationResult.INVALID_ID)
])
def test_validate_camera_password(camera_manager, camera_id, has_pwd, correct_pwd, input_pwd, expected):
    cam = camera_manager.get_camera(1)
    cam.has_password.return_value = has_pwd
    cam.password = correct_pwd
    
    assert camera_manager.validate_camera_password(camera_id, input_pwd) == expected

@pytest.mark.parametrize("camera_id, expected", [
    (1, True),
    (999, False)
])
def test_delete_camera_password(camera_manager, mock_storage_manager, camera_id, expected):
    result = camera_manager.delete_camera_password(camera_id)
    assert result is expected
    
    if expected:
        mock_storage_manager.update_camera.assert_called()