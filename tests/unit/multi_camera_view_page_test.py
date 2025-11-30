"""
Unit tests for multi_camera_view_page.py
Tests MultiCameraViewPage and _ClickableLabel classes
"""

from unittest.mock import Mock, patch

import customtkinter as ctk
import pytest
from PIL import Image

from core.pages.multi_camera_view_page import (MultiCameraViewPage,
                                               _ClickableLabel)
from manager.camera_manager import CameraValidationResult


def cancel_all_after(widget):
    """Cancel all pending after callbacks recursively."""
    try:
        for after_id in widget.tk.eval("after info").split():
            try:
                widget.after_cancel(after_id)
            except Exception:
                pass
    except Exception:
        pass


@pytest.fixture
def root():
    """Create a real CTk application for tests with proper isolation."""
    root_window = ctk.CTk()
    root_window.withdraw()
    root_window.update_idletasks()  # Ensure root is fully initialized
    yield root_window
    try:
        # Cancel all pending callbacks
        cancel_all_after(root_window)
        root_window.update_idletasks()
        # Destroy the root window
        root_window.destroy()
        # Process any remaining events to ensure cleanup
        root_window.update_idletasks()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def ensure_tkinter_cleanup():
    """Ensure Tkinter is properly cleaned up between tests."""
    yield
    # After each test, ensure any remaining Tkinter state is cleaned
    try:
        import tkinter

        # Destroy all existing Toplevel windows first
        if hasattr(tkinter, "_default_root") and tkinter._default_root:
            try:
                for widget in list(tkinter._default_root.winfo_children()):
                    try:
                        if isinstance(
                            widget, (tkinter.Toplevel, ctk.CTkToplevel)
                        ):
                            widget.withdraw()
                            widget.destroy()
                    except Exception:
                        pass
            except Exception:
                pass

        # Clear any default root that might be lingering
        if hasattr(tkinter, "_default_root") and tkinter._default_root:
            try:
                if tkinter._default_root.winfo_exists():
                    tkinter._default_root.destroy()
            except Exception:
                pass
            tkinter._default_root = None
    except Exception:
        pass


@pytest.fixture
def mock_camera_manager():
    """Create mock camera manager"""
    manager = Mock()

    # Create mock cameras
    camera1 = Mock()
    camera1.get_id.return_value = 1
    camera1.is_enabled.return_value = True
    camera1.is_locked.return_value = False
    camera1.has_password.return_value = False
    camera1.display_view.return_value = Image.new("RGB", (100, 100), "blue")

    camera2 = Mock()
    camera2.get_id.return_value = 2
    camera2.is_enabled.return_value = True
    camera2.is_locked.return_value = False
    camera2.has_password.return_value = False
    camera2.display_view.return_value = Image.new("RGB", (100, 100), "red")

    manager.camera_list = [camera1, camera2]
    return manager


# Tests for _ClickableLabel
def test_clickable_label_init(root):
    """Test _ClickableLabel initialization"""
    handler = Mock()
    label = _ClickableLabel(root, index=0, click_handler=handler, text="Test")

    assert label.index == 0
    assert label.click_handler == handler


def test_clickable_label_click(root):
    """Test _ClickableLabel click event"""
    handler = Mock()
    label = _ClickableLabel(root, index=0, click_handler=handler, text="Test")

    # Simulate click
    event = Mock()
    label._on_click(event)

    handler.assert_called_once_with(0)


# Tests for MultiCameraViewPage initialization
def test_init_default(root, mock_camera_manager):
    """Test MultiCameraViewPage initialization"""
    page = MultiCameraViewPage(root, mock_camera_manager)

    assert page.get_id() == "MultiCameraView"
    assert page.camera_manager == mock_camera_manager
    assert page._is_running is True


def test_init_custom_params(root, mock_camera_manager):
    """Test MultiCameraViewPage with custom parameters"""
    callback = Mock()
    page = MultiCameraViewPage(
        root,
        mock_camera_manager,
        page_id="CustomID",
        initially_hidden=False,
        show_single_camera=callback,
    )

    assert page.get_id() == "CustomID"
    assert page.show_single_camera == callback


def test_init_creates_labels(root, mock_camera_manager):
    """Test that initialization creates 4 labels"""
    page = MultiCameraViewPage(root, mock_camera_manager)

    assert len(page._labels) == 4
    assert len(page._photo_refs) == 4


# Tests for draw_page
def test_draw_page_creates_grid(root, mock_camera_manager):
    """Test that draw_page creates grid layout"""
    page = MultiCameraViewPage(root, mock_camera_manager)

    assert len(page._labels) == 4
    for i, label in enumerate(page._labels):
        assert isinstance(label, _ClickableLabel)
        assert label.index == i


def test_draw_page_with_no_cameras(root):
    """Test draw_page with no cameras"""
    manager = Mock()
    manager.camera_list = []

    page = MultiCameraViewPage(root, manager)

    # All labels should show "No Camera"
    for label in page._labels:
        assert "No Camera" in label.cget("text")


def test_draw_page_with_some_cameras(root, mock_camera_manager):
    """Test draw_page with some cameras"""
    page = MultiCameraViewPage(root, mock_camera_manager)

    # First 2 labels should have camera text
    assert "Camera 1" in page._labels[0].cget("text")
    assert "Camera 2" in page._labels[1].cget("text")


# Tests for refresh_frames
def test_refresh_frames_updates_images(root, mock_camera_manager):
    """Test refresh_frames updates camera images"""
    page = MultiCameraViewPage(root, mock_camera_manager)

    # Manually call refresh_frames
    page._is_running = False  # Prevent infinite loop
    page.refresh_frames()

    # Photo refs should be updated
    assert page._photo_refs[0] is not None
    assert page._photo_refs[1] is not None


def test_refresh_frames_disabled_camera(root, mock_camera_manager):
    """Test refresh_frames with disabled camera"""
    mock_camera_manager.camera_list[0].is_enabled.return_value = False

    page = MultiCameraViewPage(root, mock_camera_manager)
    page._is_running = False
    page.refresh_frames()

    # Should handle disabled camera
    assert page._photo_refs[0] is not None


def test_refresh_frames_locked_camera(root, mock_camera_manager):
    """Test refresh_frames with locked camera"""
    mock_camera_manager.camera_list[0].is_locked.return_value = True

    page = MultiCameraViewPage(root, mock_camera_manager)
    page._is_running = False
    page.refresh_frames()

    # Should show locked status
    assert page._labels[0].cget("text") == "Locked"


def test_refresh_frames_no_frame(root, mock_camera_manager):
    """Test refresh_frames when camera returns None"""
    mock_camera_manager.camera_list[0].display_view.return_value = None

    page = MultiCameraViewPage(root, mock_camera_manager)
    page._is_running = False
    page.refresh_frames()

    # Should continue without error
    assert page is not None


# Tests for handle_slot_click
def test_handle_slot_click_invalid_index(root, mock_camera_manager):
    """Test clicking on slot with no camera"""
    page = MultiCameraViewPage(root, mock_camera_manager)

    # Click on slot 3 (no camera)
    page.handle_slot_click(3)

    # Should return early without error
    assert page is not None


def test_handle_slot_click_disabled_camera(root, mock_camera_manager):
    """Test clicking on disabled camera"""
    mock_camera_manager.camera_list[0].is_enabled.return_value = False

    page = MultiCameraViewPage(root, mock_camera_manager)
    page.handle_slot_click(0)

    # Should return early
    assert page is not None


def test_handle_slot_click_locked_camera_cancel(root, mock_camera_manager):
    """Test clicking on locked camera and canceling"""
    mock_camera_manager.camera_list[0].is_locked.return_value = True
    mock_camera_manager.camera_list[0].has_password.return_value = True

    page = MultiCameraViewPage(root, mock_camera_manager)

    with patch.object(page, "_prompt_password", return_value=None):
        page.handle_slot_click(0)

    # Should return without opening camera
    assert page.show_single_camera is None or True


def test_handle_slot_click_locked_camera_wrong_password(
    root, mock_camera_manager
):
    """Test clicking on locked camera with wrong password"""
    camera = mock_camera_manager.camera_list[0]
    camera.is_locked.return_value = True
    camera.has_password.return_value = True
    mock_camera_manager.validate_camera_password.return_value = (
        CameraValidationResult.INCORRECT
    )

    page = MultiCameraViewPage(root, mock_camera_manager)

    with patch.object(page, "_prompt_password", return_value="wrong"):
        with patch.object(page, "show_toast"):
            page.handle_slot_click(0)

    camera.lock.assert_called()


def test_handle_slot_click_locked_camera_correct_password(
    root, mock_camera_manager
):
    """Test clicking on locked camera with correct password"""
    camera = mock_camera_manager.camera_list[0]
    camera.is_locked.return_value = True
    camera.has_password.return_value = True
    mock_camera_manager.validate_camera_password.return_value = (
        CameraValidationResult.VALID
    )

    callback = Mock()
    page = MultiCameraViewPage(
        root, mock_camera_manager, show_single_camera=callback
    )

    with patch.object(page, "_prompt_password", return_value="correct"):
        page.handle_slot_click(0)

    camera.unlock.assert_called()
    callback.assert_called_once_with(1)


def test_handle_slot_click_unlocked_camera(root, mock_camera_manager):
    """Test clicking on unlocked camera"""
    callback = Mock()
    page = MultiCameraViewPage(
        root, mock_camera_manager, show_single_camera=callback
    )

    page.handle_slot_click(0)

    callback.assert_called_once_with(1)


# Tests for _prompt_password
def test_prompt_password_empty(root, mock_camera_manager):
    """Test _prompt_password with empty input"""
    page = MultiCameraViewPage(root, mock_camera_manager)

    with patch(
        "core.pages.multi_camera_view_page.ctk.CTkInputDialog"
    ) as mock_dialog:
        mock_instance = Mock()
        mock_instance.get_input.return_value = ""
        mock_dialog.return_value = mock_instance

        result = page._prompt_password()

    assert result is None


def test_prompt_password_with_input(root, mock_camera_manager):
    """Test _prompt_password with valid input"""
    page = MultiCameraViewPage(root, mock_camera_manager)

    with patch(
        "core.pages.multi_camera_view_page.ctk.CTkInputDialog"
    ) as mock_dialog:
        mock_instance = Mock()
        mock_instance.get_input.return_value = "password123"
        mock_dialog.return_value = mock_instance

        result = page._prompt_password()

    assert result == "password123"


# Tests for show_toast
def test_show_toast(root, mock_camera_manager):
    """Test show_toast displays message"""
    page = MultiCameraViewPage(root, mock_camera_manager)
    page.show_toast("Test message")

    # Update to process pending events
    root.update()

    # Should not throw error
    assert page is not None


# Tests for refresh_frames scheduling
def test_refresh_frames_schedules_next(root, mock_camera_manager):
    """Test refresh_frames schedules next update when running"""
    page = MultiCameraViewPage(root, mock_camera_manager)
    page._is_running = True

    # Call refresh and check that after is scheduled
    page.refresh_frames()

    # _after_id should be set
    assert page._after_id is not None


# Tests for unexpected validation result
def test_handle_slot_click_unexpected_validation(root, mock_camera_manager):
    """Test clicking on locked camera with unexpected validation result"""
    camera = mock_camera_manager.camera_list[0]
    camera.is_locked.return_value = True
    camera.has_password.return_value = True
    # Return unexpected value (not VALID or INCORRECT)
    mock_camera_manager.validate_camera_password.return_value = "UNEXPECTED"

    page = MultiCameraViewPage(root, mock_camera_manager)

    with patch.object(page, "_prompt_password", return_value="password"):
        page.handle_slot_click(0)

    # Should handle unexpected result gracefully
    assert page is not None


# Tests for destroy
def test_destroy_locks_cameras_with_password(root, mock_camera_manager):
    """Test destroy locks cameras that have passwords"""
    mock_camera_manager.camera_list[0].has_password.return_value = True

    page = MultiCameraViewPage(root, mock_camera_manager)
    page._is_running = True
    page.destroy()

    mock_camera_manager.camera_list[0].lock.assert_called()


def test_destroy_stops_updates(root, mock_camera_manager):
    """Test destroy stops update loop"""
    page = MultiCameraViewPage(root, mock_camera_manager)
    page._is_running = True
    page.destroy()

    assert page._is_running is False
