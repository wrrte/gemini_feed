from unittest.mock import Mock, patch

import pytest

from database.schema.camera import CameraSchema
from device.appliance import create_camera_from_schema
from device.appliance.camera import SafeHomeCamera


@pytest.fixture
def mock_image_mod():
    with patch("device.appliance.camera.Image") as mock:
        yield mock


@pytest.fixture
def mock_image_draw():
    with patch("device.appliance.camera.ImageDraw") as mock:
        yield mock


@pytest.fixture
def mock_image_font():
    with patch("device.appliance.camera.ImageFont") as mock:
        yield mock


@pytest.fixture
def mock_os():
    with patch("device.appliance.camera.os") as mock:
        # Setup paths to mock file existence checks
        mock.path.dirname.return_value = "/root/device/appliance"
        mock.path.abspath.side_effect = lambda x: x
        mock.path.join.side_effect = lambda *args: "/".join(args)
        yield mock


@pytest.fixture
def camera(mock_image_mod, mock_image_font, mock_os):
    """Returns a basic camera instance with ID 0 (default image)."""
    return SafeHomeCamera(camera_id=0)


def test_init_defaults(camera):
    assert camera.camera_id == 0
    assert camera.get_location() == (0, 0)
    assert camera.pan == 0
    assert camera.zoom_setting == 1
    assert camera.has_password() is False
    assert camera.is_enabled() is False


def test_init_load_image_specific_id(mock_image_mod, mock_os):
    """Test loading specific camera images (ID 1, 2, 3)."""
    SafeHomeCamera(camera_id=1)
    # Check if Image.open was called with correct path for camera1
    args, _ = mock_image_mod.open.call_args
    assert "camera1.jpg" in args[0]


def test_init_load_image_file_not_found(mock_image_mod, mock_os):
    """Test handling of missing image files."""
    mock_image_mod.open.side_effect = FileNotFoundError
    cam = SafeHomeCamera(camera_id=1)
    assert cam.image is None


def test_location_setters(camera):
    assert camera.set_location((10, 20)) is True
    assert camera.get_location() == (10, 20)
    # Set same location, should return False
    assert camera.set_location((10, 20)) is False


def test_id_setter(camera, mock_image_mod):
    assert camera.set_id(2) is True
    assert camera.get_id() == 2
    # Verify image reload attempt
    assert mock_image_mod.open.call_count > 0

    # Set same ID
    assert camera.set_id(2) is False


def test_pan_operations(camera):
    # Test Pan Right
    camera.pan = 0
    assert camera.pan_right() is True
    assert camera.pan == 1

    # Max Pan
    camera.pan = SafeHomeCamera.MAX_PAN
    assert camera.pan_right() is False
    assert camera.pan == SafeHomeCamera.MAX_PAN

    # Test Pan Left
    camera.pan = 0
    assert camera.pan_left() is True
    assert camera.pan == -1

    # Min Pan
    camera.pan = SafeHomeCamera.MIN_PAN
    assert camera.pan_left() is False
    assert camera.pan == SafeHomeCamera.MIN_PAN


def test_zoom_operations(camera):
    # Zoom In
    camera.zoom_setting = 1
    assert camera.zoom_in() is True
    assert camera.zoom_setting == 2

    # Max Zoom
    camera.zoom_setting = SafeHomeCamera.MAX_ZOOM
    assert camera.zoom_in() is False

    # Zoom Out
    camera.zoom_setting = 2
    assert camera.zoom_out() is True
    assert camera.zoom_setting == 1

    # Min Zoom
    camera.zoom_setting = SafeHomeCamera.MIN_ZOOM
    assert camera.zoom_out() is False


def test_password_management(camera):
    # Set password
    assert camera.set_password("secret") is True
    assert camera.has_password() is True
    assert camera.get_password() == "secret"
    assert camera.is_locked() is True

    # Unlock/Lock manually
    camera.unlock()
    assert camera.is_locked() is False
    camera.lock()
    assert camera.is_locked() is True

    # Remove password
    assert camera.set_password(None) is False
    assert camera.has_password() is False
    assert camera.get_password() is None
    assert camera.is_locked() is False


def test_enable_disable(camera):
    camera.enable()
    assert camera.is_enabled() is True
    camera.disable()
    assert camera.is_enabled() is False


def test_display_view_disabled(camera, mock_image_mod):
    camera.disable()
    mock_view = Mock()
    mock_image_mod.new.return_value = mock_view

    result = camera.display_view()

    assert result == mock_view
    # Should not attempt to crop or draw if disabled
    if camera.image:
        camera.image.crop.assert_not_called()


def test_display_view_locked(camera, mock_image_mod):
    camera.enable()
    camera.set_password("pass")  # This locks it

    # Should return black screen (new image)
    mock_image_mod.new.assert_called()


def test_display_view_success(camera, mock_image_mod, mock_image_draw):
    camera.enable()
    camera.image = Mock()
    camera.image.size = (100, 100)

    # Mock chain: crop -> resize
    mock_cropped = Mock()
    mock_resized = Mock()
    camera.image.crop.return_value = mock_cropped
    mock_cropped.resize.return_value = mock_resized

    # Setup ImageDraw mock
    mock_draw_instance = Mock()
    mock_image_draw.Draw.return_value = mock_draw_instance
    mock_draw_instance.textbbox.return_value = (0, 0, 50, 20)

    # Verify image manipulation pipeline
    camera.image.crop.assert_called()
    mock_cropped.resize.assert_called()

    # Verify overlay drawing
    mock_draw_instance.rounded_rectangle.assert_called()
    mock_draw_instance.text.assert_called()


def test_display_view_load_image_lazy(camera, mock_image_mod, mock_os):
    """Test that image is loaded if None during display_view."""
    camera.image = None
    camera.enable()

    # Mock successful load
    mock_loaded_img = Mock()
    mock_loaded_img.size = (100, 100)
    mock_image_mod.open.return_value = mock_loaded_img

    # Setup crop/resize mocks on the NEW loaded image
    mock_cropped = Mock()
    mock_loaded_img.crop.return_value = mock_cropped
    mock_cropped.resize.return_value = Mock()

    camera.display_view()

    mock_image_mod.open.assert_called()
    assert camera.image is not None


def test_display_view_pan_labels(camera, mock_image_mod, mock_image_draw):
    """Test branches for panning label generation (right, left, center)."""
    camera.enable()
    camera.image = Mock()
    camera.image.size = (100, 100)
    mock_draw = Mock()
    mock_image_draw.Draw.return_value = mock_draw
    mock_draw.textbbox.return_value = (0, 0, 10, 10)

    # Test Pan Right logic
    camera.pan = 1
    camera.display_view()

    # Test Pan Left logic
    camera.pan = -1
    camera.display_view()

    # Test Center logic
    camera.pan = 0
    camera.display_view()


def test_to_schema(camera):
    schema = camera.to_schema()
    assert isinstance(schema, CameraSchema)
    assert schema.camera_id == camera.camera_id


def test_get_info(camera):
    info = camera.get_info()
    assert "camera_id" in info
    assert "locked" in info
    assert info["locked"] is False


def test_create_camera_from_schema():
    """Test creating a camera instance from a schema."""
    schema = CameraSchema(
        camera_id=5,
        coordinate_x=10,
        coordinate_y=20,
        pan=1,
        zoom_setting=2,
        has_password=True,
        password="secret_pass",
        enabled=True
    )

    cam = create_camera_from_schema(schema)

    assert cam.camera_id == 5
    assert cam.get_location() == (10, 20)
    assert cam.pan == 1
    assert cam.zoom_setting == 2
    assert cam.has_password() is True
    assert cam.get_password() == "secret_pass"
    assert cam.is_enabled() is True
    assert cam.is_locked() is True  # Should be locked if password exists


def test_create_camera_from_schema_no_password():
    """Test creating a camera instance from a schema without password."""
    schema = CameraSchema(
        camera_id=6,
        coordinate_x=5,
        coordinate_y=5,
        pan=0,
        zoom_setting=1,
        has_password=False,
        password=None,
        enabled=True
    )

    cam = create_camera_from_schema(schema)

    assert cam.camera_id == 6
    assert cam.has_password() is False
    assert cam.get_password() is None
    assert cam.is_locked() is False  # Should be unlocked if no password
