"""
Unit tests for single_camera_view_page.py
Tests SingleCameraViewPage class with 100% coverage
"""

from unittest.mock import Mock, patch

import customtkinter as ctk
import pytest
from PIL import Image

from core.pages.single_camera_view_page import SingleCameraViewPage
from database.schema.camera import CameraControlType


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
def mock_camera():
    """Create a mock camera."""
    camera = Mock()
    camera.get_id.return_value = 1
    camera.is_enabled.return_value = True
    camera.is_locked.return_value = False
    camera.has_password.return_value = False

    # Create a real image for display_view
    real_img = Image.new("RGB", (500, 500), color="blue")
    camera.display_view.return_value = real_img

    camera.zoom_setting = 1.0
    camera.pan = 0
    camera.enabled = True
    return camera


@pytest.fixture
def mock_camera_manager(mock_camera):
    """Create a mock CameraManager."""
    manager = Mock()
    manager.get_camera.return_value = mock_camera
    manager.camera_list = [mock_camera]
    manager.control_single_camera.return_value = True
    return manager


# =============================================================================
# Init tests (with mocked draw_page to avoid image issues in some tests)
# =============================================================================


def test_init_default(root, mock_camera_manager):
    """Test basic initialization."""
    with patch.object(SingleCameraViewPage, "draw_page"):
        with patch.object(SingleCameraViewPage, "update_view"):
            page = SingleCameraViewPage(
                root, camera_manager=mock_camera_manager, camera_id=1
            )
            assert page.camera_id == 1
            assert page.camera_manager == mock_camera_manager
            page.destroy()


def test_init_no_camera_id(root, mock_camera_manager):
    """Test initialization without camera_id."""
    with patch.object(SingleCameraViewPage, "draw_page"):
        with patch.object(SingleCameraViewPage, "update_view"):
            page = SingleCameraViewPage(
                root, camera_manager=mock_camera_manager
            )
            assert page.camera_id is None
            page.destroy()


def test_init_custom_page_id(root, mock_camera_manager):
    """Test initialization with custom page_id."""
    with patch.object(SingleCameraViewPage, "draw_page"):
        with patch.object(SingleCameraViewPage, "update_view"):
            page = SingleCameraViewPage(
                root, page_id="custom", camera_manager=mock_camera_manager
            )
            assert page.get_id() == "custom"
            page.destroy()


def test_init_initially_hidden(root, mock_camera_manager):
    """Test initialization with initially_hidden."""
    with patch.object(SingleCameraViewPage, "draw_page"):
        with patch.object(SingleCameraViewPage, "update_view"):
            page = SingleCameraViewPage(
                root,
                camera_manager=mock_camera_manager,
                initially_hidden=True,
            )
            page.destroy()


# =============================================================================
# Control tests
# =============================================================================


def test_pan_left(root, mock_camera_manager, mock_camera):
    """Test pan_left calls camera manager."""
    with patch.object(SingleCameraViewPage, "draw_page"):
        with patch.object(SingleCameraViewPage, "update_view"):
            page = SingleCameraViewPage(
                root, camera_manager=mock_camera_manager
            )
            page.camera_id = 1
            page.pan_left()
            mock_camera_manager.control_single_camera.assert_called_with(
                1, CameraControlType.PAN_LEFT
            )
            page.destroy()


def test_pan_left_disabled(root, mock_camera_manager, mock_camera):
    """Test pan_left when camera is disabled."""
    mock_camera.is_enabled.return_value = False
    with patch.object(SingleCameraViewPage, "draw_page"):
        with patch.object(SingleCameraViewPage, "update_view"):
            page = SingleCameraViewPage(
                root, camera_manager=mock_camera_manager
            )
            page.camera_id = 1
            page.pan_left()
            mock_camera_manager.control_single_camera.assert_not_called()
            page.destroy()


def test_pan_left_no_camera(root, mock_camera_manager):
    """Test pan_left when camera doesn't exist."""
    mock_camera_manager.get_camera.return_value = None
    with patch.object(SingleCameraViewPage, "draw_page"):
        with patch.object(SingleCameraViewPage, "update_view"):
            page = SingleCameraViewPage(
                root, camera_manager=mock_camera_manager
            )
            page.camera_id = 1
            page.pan_left()
            mock_camera_manager.control_single_camera.assert_not_called()
            page.destroy()


def test_pan_right(root, mock_camera_manager, mock_camera):
    """Test pan_right calls camera manager."""
    with patch.object(SingleCameraViewPage, "draw_page"):
        with patch.object(SingleCameraViewPage, "update_view"):
            page = SingleCameraViewPage(
                root, camera_manager=mock_camera_manager
            )
            page.camera_id = 1
            page.pan_right()
            mock_camera_manager.control_single_camera.assert_called_with(
                1, CameraControlType.PAN_RIGHT
            )
            page.destroy()


def test_pan_right_disabled(root, mock_camera_manager, mock_camera):
    """Test pan_right when camera is disabled."""
    mock_camera.is_enabled.return_value = False
    with patch.object(SingleCameraViewPage, "draw_page"):
        with patch.object(SingleCameraViewPage, "update_view"):
            page = SingleCameraViewPage(
                root, camera_manager=mock_camera_manager
            )
            page.camera_id = 1
            page.pan_right()
            mock_camera_manager.control_single_camera.assert_not_called()
            page.destroy()


def test_zoom_in(root, mock_camera_manager, mock_camera):
    """Test zoom_in calls camera manager."""
    with patch.object(SingleCameraViewPage, "draw_page"):
        with patch.object(SingleCameraViewPage, "update_view"):
            page = SingleCameraViewPage(
                root, camera_manager=mock_camera_manager
            )
            page.camera_id = 1
            page.zoom_in()
            mock_camera_manager.control_single_camera.assert_called_with(
                1, CameraControlType.ZOOM_IN
            )
            page.destroy()


def test_zoom_in_disabled(root, mock_camera_manager, mock_camera):
    """Test zoom_in when camera is disabled."""
    mock_camera.is_enabled.return_value = False
    with patch.object(SingleCameraViewPage, "draw_page"):
        with patch.object(SingleCameraViewPage, "update_view"):
            page = SingleCameraViewPage(
                root, camera_manager=mock_camera_manager
            )
            page.camera_id = 1
            page.zoom_in()
            mock_camera_manager.control_single_camera.assert_not_called()
            page.destroy()


def test_zoom_out(root, mock_camera_manager, mock_camera):
    """Test zoom_out calls camera manager."""
    with patch.object(SingleCameraViewPage, "draw_page"):
        with patch.object(SingleCameraViewPage, "update_view"):
            page = SingleCameraViewPage(
                root, camera_manager=mock_camera_manager
            )
            page.camera_id = 1
            page.zoom_out()
            mock_camera_manager.control_single_camera.assert_called_with(
                1, CameraControlType.ZOOM_OUT
            )
            page.destroy()


def test_zoom_out_disabled(root, mock_camera_manager, mock_camera):
    """Test zoom_out when camera is disabled."""
    mock_camera.is_enabled.return_value = False
    with patch.object(SingleCameraViewPage, "draw_page"):
        with patch.object(SingleCameraViewPage, "update_view"):
            page = SingleCameraViewPage(
                root, camera_manager=mock_camera_manager
            )
            page.camera_id = 1
            page.zoom_out()
            mock_camera_manager.control_single_camera.assert_not_called()
            page.destroy()


# =============================================================================
# destroy tests
# =============================================================================


def test_destroy_with_password(root, mock_camera_manager, mock_camera):
    """Test destroy locks camera if it has password."""
    mock_camera.has_password.return_value = True
    with patch.object(SingleCameraViewPage, "draw_page"):
        with patch.object(SingleCameraViewPage, "update_view"):
            page = SingleCameraViewPage(
                root, camera_manager=mock_camera_manager
            )
            page.camera_id = 1
            page.destroy()
            mock_camera.lock.assert_called()


def test_destroy_without_password(root, mock_camera_manager, mock_camera):
    """Test destroy doesn't lock camera if no password."""
    mock_camera.has_password.return_value = False
    with patch.object(SingleCameraViewPage, "draw_page"):
        with patch.object(SingleCameraViewPage, "update_view"):
            page = SingleCameraViewPage(
                root, camera_manager=mock_camera_manager
            )
            page.camera_id = 1
            page.destroy()
            mock_camera.lock.assert_not_called()


def test_destroy_no_camera(root, mock_camera_manager):
    """Test destroy handles missing camera."""
    mock_camera_manager.get_camera.return_value = None
    with patch.object(SingleCameraViewPage, "draw_page"):
        with patch.object(SingleCameraViewPage, "update_view"):
            page = SingleCameraViewPage(
                root, camera_manager=mock_camera_manager
            )
            page.camera_id = 1
            page.destroy()  # Should not crash


def test_destroy_cancels_after(root, mock_camera_manager):
    """Test destroy cancels pending after callbacks."""
    with patch.object(SingleCameraViewPage, "draw_page"):
        with patch.object(SingleCameraViewPage, "update_view"):
            page = SingleCameraViewPage(
                root, camera_manager=mock_camera_manager
            )
            page._after_id = 123
            with patch.object(page, "after_cancel") as mock_cancel:
                page.destroy()
                mock_cancel.assert_called_with(123)


def test_destroy_sets_running_false(root, mock_camera_manager):
    """Test destroy sets _is_running to False."""
    with patch.object(SingleCameraViewPage, "draw_page"):
        with patch.object(SingleCameraViewPage, "update_view"):
            page = SingleCameraViewPage(
                root, camera_manager=mock_camera_manager
            )
            page._is_running = True
            page.destroy()
            assert page._is_running is False


# =============================================================================
# Real GUI tests - draw_page and update_view
# =============================================================================


def test_draw_page_creates_widgets(root, mock_camera_manager, mock_camera):
    """Test draw_page creates all required widgets."""
    with patch.object(SingleCameraViewPage, "update_view"):
        page = SingleCameraViewPage(
            root, camera_manager=mock_camera_manager, camera_id=1
        )
        root.update_idletasks()

        # Check that image_label exists
        assert hasattr(page, "image_label")
        assert hasattr(page, "status_label")
        assert hasattr(page, "_buttons")
        assert len(page._buttons) == 4  # 4 control buttons

        page._is_running = False
        cancel_all_after(page)
        page.destroy()


def test_draw_page_buttons_work(root, mock_camera_manager, mock_camera):
    """Test that control buttons are functional."""
    with patch.object(SingleCameraViewPage, "update_view"):
        page = SingleCameraViewPage(
            root, camera_manager=mock_camera_manager, camera_id=1
        )
        root.update_idletasks()

        # Invoke pan left button
        page._buttons[0].invoke()
        root.update_idletasks()

        mock_camera_manager.control_single_camera.assert_called()

        page._is_running = False
        cancel_all_after(page)
        page.destroy()


def test_update_view_displays_image(root, mock_camera_manager, mock_camera):
    """Test update_view displays camera image."""
    with patch.object(SingleCameraViewPage, "update_view"):
        page = SingleCameraViewPage(
            root, camera_manager=mock_camera_manager, camera_id=1
        )
        root.update_idletasks()

    # Now call update_view directly (not through after)
    page._is_running = False  # Prevent scheduling next update
    SingleCameraViewPage.update_view(page)
    root.update_idletasks()

    # Check status was updated
    assert "Camera ID: 1" in page.status_label.cget("text")

    cancel_all_after(page)
    page.destroy()


def test_update_view_with_locked_camera(
    root, mock_camera_manager, mock_camera
):
    """Test update_view destroys page if camera is locked."""
    # First check: camera is None or is_locked() returns True
    mock_camera.is_locked.return_value = True

    with patch.object(SingleCameraViewPage, "update_view"):
        page = SingleCameraViewPage(
            root, camera_manager=mock_camera_manager, camera_id=1
        )
        root.update_idletasks()

    page._is_running = False
    # Don't patch update_view - call it directly to test the locked camera path
    with patch.object(page, "destroy") as mock_destroy:
        page.update_view()
        mock_destroy.assert_called()

    cancel_all_after(page)


def test_update_view_with_locked_camera_second_check(
    root, mock_camera_manager, mock_camera
):
    """
    Test update_view destroys page if camera is locked
    (second check at lines 225-227).
    """
    # This test covers the second is_locked() check at lines 225-227
    # We need camera to not be None and not
    #  locked initially, then become locked.
    mock_camera.is_locked.return_value = False

    with patch.object(SingleCameraViewPage, "update_view"):
        page = SingleCameraViewPage(
            root, camera_manager=mock_camera_manager, camera_id=1
        )
        root.update_idletasks()

    # Now make camera locked for the second check
    mock_camera.is_locked.return_value = True
    page._is_running = False

    with patch.object(page, "destroy") as mock_destroy:
        page.update_view()
        mock_destroy.assert_called()

    cancel_all_after(page)


def test_update_view_with_no_camera(root, mock_camera_manager):
    """Test update_view destroys page if camera is None."""
    mock_camera_manager.get_camera.return_value = None

    with patch.object(SingleCameraViewPage, "update_view"):
        page = SingleCameraViewPage(
            root, camera_manager=mock_camera_manager, camera_id=1
        )
        root.update_idletasks()

    page._is_running = False
    with patch.object(page, "destroy") as mock_destroy:
        SingleCameraViewPage.update_view(page)
        mock_destroy.assert_called()

    cancel_all_after(page)


def test_update_view_resizes_image(root, mock_camera_manager, mock_camera):
    """Test update_view resizes image if needed."""
    # Return an image with different size
    small_img = Image.new("RGB", (100, 100), color="red")
    mock_camera.display_view.return_value = small_img

    with patch.object(SingleCameraViewPage, "update_view"):
        page = SingleCameraViewPage(
            root, camera_manager=mock_camera_manager, camera_id=1
        )
        root.update_idletasks()

    page._is_running = False
    SingleCameraViewPage.update_view(page)
    root.update_idletasks()

    cancel_all_after(page)
    page.destroy()


def test_update_view_handles_none_image(
    root, mock_camera_manager, mock_camera
):
    """Test update_view handles None image."""
    mock_camera.display_view.return_value = None

    with patch.object(SingleCameraViewPage, "update_view"):
        page = SingleCameraViewPage(
            root, camera_manager=mock_camera_manager, camera_id=1
        )
        root.update_idletasks()

    page._is_running = False
    SingleCameraViewPage.update_view(page)  # Should not crash
    root.update_idletasks()

    cancel_all_after(page)
    page.destroy()


def test_update_view_handles_display_error(
    root, mock_camera_manager, mock_camera
):
    """Test update_view handles display error."""
    mock_camera.display_view.side_effect = Exception("Display error")

    with patch.object(SingleCameraViewPage, "update_view"):
        page = SingleCameraViewPage(
            root, camera_manager=mock_camera_manager, camera_id=1
        )
        root.update_idletasks()

    page._is_running = False
    page.update_count = 1
    SingleCameraViewPage.update_view(page)  # Should not crash
    root.update_idletasks()

    cancel_all_after(page)
    page.destroy()


def test_update_view_handles_status_error(
    root, mock_camera_manager, mock_camera
):
    """Test update_view handles status update error."""
    mock_camera.get_id.side_effect = Exception("ID error")

    with patch.object(SingleCameraViewPage, "update_view"):
        page = SingleCameraViewPage(
            root, camera_manager=mock_camera_manager, camera_id=1
        )
        root.update_idletasks()

    page._is_running = False
    page.update_count = 1
    SingleCameraViewPage.update_view(page)  # Should not crash
    root.update_idletasks()

    cancel_all_after(page)
    page.destroy()


def test_update_view_pan_right_status(root, mock_camera_manager, mock_camera):
    """Test update_view shows pan right in status."""
    mock_camera.pan = 5

    with patch.object(SingleCameraViewPage, "update_view"):
        page = SingleCameraViewPage(
            root, camera_manager=mock_camera_manager, camera_id=1
        )
        root.update_idletasks()

    page._is_running = False
    SingleCameraViewPage.update_view(page)
    root.update_idletasks()

    assert "Right" in page.status_label.cget("text")

    cancel_all_after(page)
    page.destroy()


def test_update_view_pan_left_status(root, mock_camera_manager, mock_camera):
    """Test update_view shows pan left in status."""
    mock_camera.pan = -5

    with patch.object(SingleCameraViewPage, "update_view"):
        page = SingleCameraViewPage(
            root, camera_manager=mock_camera_manager, camera_id=1
        )
        root.update_idletasks()

    page._is_running = False
    SingleCameraViewPage.update_view(page)
    root.update_idletasks()

    assert "Left" in page.status_label.cget("text")

    cancel_all_after(page)
    page.destroy()


def test_update_view_disables_buttons_when_camera_disabled(
    root, mock_camera_manager, mock_camera
):
    """Test update_view disables buttons when camera is disabled."""
    mock_camera.is_enabled.return_value = False

    with patch.object(SingleCameraViewPage, "update_view"):
        page = SingleCameraViewPage(
            root, camera_manager=mock_camera_manager, camera_id=1
        )
        root.update_idletasks()

    page._is_running = False
    SingleCameraViewPage.update_view(page)
    root.update_idletasks()

    # Check buttons are disabled
    for btn in page._buttons:
        assert btn.cget("state") == "disabled"

    cancel_all_after(page)
    page.destroy()


def test_update_view_schedules_next_update(
    root, mock_camera_manager, mock_camera
):
    """Test update_view schedules next update when running."""
    with patch.object(SingleCameraViewPage, "update_view"):
        page = SingleCameraViewPage(
            root, camera_manager=mock_camera_manager, camera_id=1
        )
        root.update_idletasks()

    page._is_running = True
    page._after_id = None

    with patch.object(page, "after", return_value=999) as mock_after:
        SingleCameraViewPage.update_view(page)

    assert page._after_id == 999
    mock_after.assert_called()

    page._is_running = False
    cancel_all_after(page)
    page.destroy()


def test_update_view_error_suppressed_after_count(
    root, mock_camera_manager, mock_camera
):
    """Test update_view suppresses errors after count > 3."""
    mock_camera.display_view.side_effect = Exception("Error")

    with patch.object(SingleCameraViewPage, "update_view"):
        page = SingleCameraViewPage(
            root, camera_manager=mock_camera_manager, camera_id=1
        )
        root.update_idletasks()

    page._is_running = False
    page.update_count = 10  # High count, errors suppressed

    # Should not print error
    SingleCameraViewPage.update_view(page)
    root.update_idletasks()

    cancel_all_after(page)
    page.destroy()
