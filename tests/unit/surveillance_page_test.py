"""
Unit tests for surveillance_page.py
Tests SurveillancePage class with 100% coverage
"""

from unittest.mock import Mock, patch

import customtkinter as ctk
import pytest

from core.pages.surveillance_page import SurveillancePage
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


@pytest.fixture
def mock_camera():
    camera = Mock()
    camera.get_id.return_value = 1
    camera.is_enabled.return_value = True
    camera.is_locked.return_value = False
    camera.has_password.return_value = False
    camera.coordinate_x = 100
    camera.coordinate_y = 100
    return camera


@pytest.fixture
def mock_camera_manager(mock_camera):
    manager = Mock()
    manager.camera_list = [mock_camera]
    manager.get_camera.return_value = mock_camera
    manager.enable_camera.return_value = True
    manager.disable_camera.return_value = True
    manager.validate_camera_password.return_value = (
        CameraValidationResult.VALID
    )
    manager.set_password.return_value = True
    manager.change_password.return_value = True
    manager.get_all_camera_info.return_value = [
        {
            "camera_id": 1,
            "enabled": True,
            "has_password": False,
            "locked": False,
            "coordinate_x": 100,
            "coordinate_y": 100,
        }
    ]
    return manager


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


@pytest.fixture(autouse=True)
def mock_draw_floor_plan():
    with patch("core.pages.surveillance_page.draw_floor_plan"):
        yield


@pytest.fixture(autouse=True)
def mock_ctk_input_dialog():
    """Mock CTkInputDialog to prevent actual dialog"""
    with patch("customtkinter.CTkInputDialog") as mock:
        mock.return_value.get_input.return_value = None
        yield mock


def _setup_page(page):
    """Setup common page attributes"""
    page._selected_cam_index = 0
    page.selected_camera_id = 1


# =============================================================================
# Init tests
# =============================================================================


def test_init(root, mock_camera_manager):
    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    assert page.get_id() == "surveillance"
    cancel_all_after(page)


def test_init_with_callbacks(root, mock_camera_manager):
    show_multi = Mock()
    show_single = Mock()
    page = SurveillancePage(
        root,
        "surveillance",
        mock_camera_manager,
        show_multi_camera=show_multi,
        show_single_camera=show_single,
    )
    assert page.show_multi_camera == show_multi
    cancel_all_after(page)


# =============================================================================
# draw_page tests
# =============================================================================


def test_draw_page(root, mock_camera_manager):
    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    assert page.left_panel is not None
    assert page.canvas is not None
    cancel_all_after(page)


def test_draw_page_with_has_password(root, mock_camera_manager):
    """Test draw_page when camera has password"""
    mock_camera_manager.get_all_camera_info.return_value = [
        {
            "camera_id": 1,
            "enabled": True,
            "has_password": True,
            "locked": True,
            "coordinate_x": 100,
            "coordinate_y": 100,
        }
    ]
    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    assert len(page._locked_lbls) == 1
    cancel_all_after(page)


# =============================================================================
# _on_canvas_ready tests
# =============================================================================


def test_on_canvas_ready(root, mock_camera_manager):
    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    page._on_canvas_ready()
    assert hasattr(page, "_fp_job")
    cancel_all_after(page)


def test_on_canvas_ready_debounce(root, mock_camera_manager):
    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    page._fp_job = page.canvas.after(1000, lambda: None)
    page._on_canvas_ready()
    cancel_all_after(page)


def test_on_canvas_ready_render_executed(root, mock_camera_manager):
    """Test that _render function is scheduled after delay"""
    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    page._on_canvas_ready()
    # Verify _fp_job was scheduled
    assert hasattr(page, "_fp_job")
    assert page._fp_job is not None
    # Process only idle tasks, not all events (prevents hanging on UI events)
    # Use update_idletasks() instead of update() to avoid waiting for UI events
    root.update_idletasks()
    # Cancel the job immediately to prevent it from running
    # and causing UI issues.
    if hasattr(page, "_fp_job") and page._fp_job:
        try:
            page.canvas.after_cancel(page._fp_job)
        except Exception:
            pass
    cancel_all_after(page)


def test_render_function_executes_draw_methods(root, mock_camera_manager):
    """
    Test that _render function actually calls
    _draw_floor_plan and _draw_cameras.
    """
    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    with (
        patch(
            "core.pages.surveillance_page.draw_floor_plan"
        ) as mock_draw_floor_util,
        patch.object(page, "_draw_cameras") as mock_draw_cameras,
    ):
        # Mock canvas.after to execute callback immediately
        original_after = page.canvas.after

        def immediate_after(delay_ms, callback):
            # Execute callback immediately instead of scheduling it
            callback()
            return original_after(delay_ms, lambda: None)  # Return a dummy ID

        with patch.object(page.canvas, "after", side_effect=immediate_after):
            # Call _on_canvas_ready to set up _render
            page._on_canvas_ready()
            root.update_idletasks()
            # Verify both methods were called by the _render callback
            mock_draw_floor_util.assert_called_with(page.canvas)
            mock_draw_cameras.assert_called()
    cancel_all_after(page)


# =============================================================================
# _draw_cameras test
# =============================================================================


def test_draw_cameras(root, mock_camera_manager):
    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    page._draw_cameras()
    cancel_all_after(page)


# =============================================================================
# _draw_floor_plan test (needs to call actual method)
# =============================================================================


def test_draw_floor_plan_calls_util(root, mock_camera_manager):
    """Test _draw_floor_plan calls the utility function"""
    with patch("core.pages.surveillance_page.draw_floor_plan") as mock_draw:
        page = SurveillancePage(root, "surveillance", mock_camera_manager)
        # Force call _draw_floor_plan directly
        page._draw_floor_plan()
        mock_draw.assert_called_with(page.canvas)
        cancel_all_after(page)


# =============================================================================
# enable_camera tests
# =============================================================================


def test_enable_camera_success(root, mock_camera_manager):
    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    _setup_page(page)
    page.enable_camera()
    mock_camera_manager.enable_camera.assert_called()
    cancel_all_after(page)


def test_enable_camera_disabled_state(root, mock_camera_manager):
    mock_camera_manager.get_all_camera_info.return_value = [
        {
            "camera_id": 1,
            "enabled": False,
            "has_password": False,
            "locked": False,
            "coordinate_x": 100,
            "coordinate_y": 100,
        }
    ]
    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    _setup_page(page)
    page.enable_camera()
    cancel_all_after(page)


# =============================================================================
# disable_camera tests
# =============================================================================


def test_disable_camera_success(root, mock_camera_manager):
    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    _setup_page(page)
    page.disable_camera()
    mock_camera_manager.disable_camera.assert_called()
    cancel_all_after(page)


# =============================================================================
# view_cam tests
# =============================================================================


def test_view_cam_success(root, mock_camera_manager, mock_camera):
    mock_camera.is_locked.return_value = False
    show_single = Mock()

    page = SurveillancePage(
        root,
        "surveillance",
        mock_camera_manager,
        show_single_camera=show_single,
    )
    _setup_page(page)
    page.view_cam()

    show_single.assert_called_with(1)
    cancel_all_after(page)


def test_view_cam_locked_cancel(
    root, mock_camera_manager, mock_camera, mock_ctk_input_dialog
):
    mock_camera.is_locked.return_value = True
    mock_ctk_input_dialog.return_value.get_input.return_value = None

    page = SurveillancePage(
        root, "surveillance", mock_camera_manager, show_single_camera=Mock()
    )
    _setup_page(page)
    page.view_cam()
    cancel_all_after(page)


def test_view_cam_locked_empty_password(
    root, mock_camera_manager, mock_camera, mock_ctk_input_dialog
):
    mock_camera.is_locked.return_value = True
    mock_ctk_input_dialog.return_value.get_input.return_value = ""

    page = SurveillancePage(
        root, "surveillance", mock_camera_manager, show_single_camera=Mock()
    )
    _setup_page(page)
    page.view_cam()
    cancel_all_after(page)


def test_view_cam_locked_valid_password(
    root, mock_camera_manager, mock_camera, mock_ctk_input_dialog
):
    mock_camera.is_locked.return_value = True
    mock_ctk_input_dialog.return_value.get_input.return_value = "password"
    mock_camera_manager.validate_camera_password.return_value = (
        CameraValidationResult.VALID
    )
    show_single = Mock()

    page = SurveillancePage(
        root,
        "surveillance",
        mock_camera_manager,
        show_single_camera=show_single,
    )
    _setup_page(page)
    page.view_cam()

    mock_camera.unlock.assert_called()
    show_single.assert_called_with(1)
    cancel_all_after(page)


def test_view_cam_locked_incorrect_password(
    root, mock_camera_manager, mock_camera, mock_ctk_input_dialog
):
    mock_camera.is_locked.return_value = True
    mock_ctk_input_dialog.return_value.get_input.return_value = "wrong"
    mock_camera_manager.validate_camera_password.return_value = (
        CameraValidationResult.INCORRECT
    )

    with patch("core.pages.surveillance_page.show_toast") as mock_toast:
        page = SurveillancePage(
            root,
            "surveillance",
            mock_camera_manager,
            show_single_camera=Mock(),
        )
        _setup_page(page)
        page.view_cam()
        mock_toast.assert_called()
        cancel_all_after(page)


def test_view_cam_locked_unexpected_result(
    root, mock_camera_manager, mock_camera, mock_ctk_input_dialog
):
    mock_camera.is_locked.return_value = True
    mock_ctk_input_dialog.return_value.get_input.return_value = "pwd"
    mock_camera_manager.validate_camera_password.return_value = (
        CameraValidationResult.NO_PASSWORD
    )

    page = SurveillancePage(
        root, "surveillance", mock_camera_manager, show_single_camera=Mock()
    )
    _setup_page(page)
    page.view_cam()
    cancel_all_after(page)


# =============================================================================
# _prompt_password tests
# =============================================================================


def test_prompt_password_returns_value(
    root, mock_camera_manager, mock_ctk_input_dialog
):
    """Test _prompt_password returns the entered value"""
    mock_ctk_input_dialog.return_value.get_input.return_value = "testpwd"

    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    result = page._prompt_password("Title", "Text")
    assert result == "testpwd"
    cancel_all_after(page)


def test_prompt_password_empty_returns_none(
    root, mock_camera_manager, mock_ctk_input_dialog
):
    """Test _prompt_password returns None for empty input"""
    mock_ctk_input_dialog.return_value.get_input.return_value = ""

    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    result = page._prompt_password("Title", "Text")
    assert result is None
    cancel_all_after(page)


# =============================================================================
# show_toast tests
# =============================================================================


def test_show_toast_creates_toast(root, mock_camera_manager):
    """Test show_toast creates a toast notification"""
    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    root.update_idletasks()

    # Call show_toast - it creates a CTkToplevel
    page.show_toast("Test message", duration_ms=50)
    root.update_idletasks()

    # Find and hide any toast windows that were created
    for child in root.winfo_children():
        if isinstance(child, ctk.CTkToplevel):
            child.withdraw()

    cancel_all_after(page)


# =============================================================================
# set_pwd tests
# =============================================================================


def test_set_pwd_not_locked_cancel(root, mock_camera_manager, mock_camera):
    mock_camera.is_locked.return_value = False

    with patch.object(
        SurveillancePage, "_prompt_new_password", return_value=None
    ):
        page = SurveillancePage(root, "surveillance", mock_camera_manager)
        _setup_page(page)
        page.set_pwd()
        cancel_all_after(page)


def test_set_pwd_locked_cancel(
    root, mock_camera_manager, mock_camera, mock_ctk_input_dialog
):
    mock_camera.is_locked.return_value = True
    mock_ctk_input_dialog.return_value.get_input.return_value = None

    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    _setup_page(page)
    page.set_pwd()
    cancel_all_after(page)


def test_set_pwd_locked_incorrect(
    root, mock_camera_manager, mock_camera, mock_ctk_input_dialog
):
    mock_camera.is_locked.return_value = True
    mock_ctk_input_dialog.return_value.get_input.return_value = "wrong"
    mock_camera_manager.validate_camera_password.return_value = (
        CameraValidationResult.INCORRECT
    )

    with patch("core.pages.surveillance_page.show_toast") as mock_toast:
        page = SurveillancePage(root, "surveillance", mock_camera_manager)
        _setup_page(page)
        page.set_pwd()
        mock_toast.assert_called()
        cancel_all_after(page)


def test_set_pwd_locked_unexpected(
    root, mock_camera_manager, mock_camera, mock_ctk_input_dialog
):
    mock_camera.is_locked.return_value = True
    mock_ctk_input_dialog.return_value.get_input.return_value = "pwd"
    mock_camera_manager.validate_camera_password.return_value = (
        CameraValidationResult.NO_PASSWORD
    )

    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    _setup_page(page)
    page.set_pwd()
    cancel_all_after(page)


def test_set_pwd_locked_valid_then_set_new(
    root, mock_camera_manager, mock_camera, mock_ctk_input_dialog
):
    """Test set_pwd with valid current password then set new password"""
    mock_camera.is_locked.return_value = True
    mock_ctk_input_dialog.return_value.get_input.return_value = "correct"
    mock_camera_manager.validate_camera_password.return_value = (
        CameraValidationResult.VALID
    )

    with patch.object(
        SurveillancePage, "_prompt_new_password", return_value="newpwd"
    ):
        with patch("core.pages.surveillance_page.show_toast") as mock_toast:
            page = SurveillancePage(root, "surveillance", mock_camera_manager)
            _setup_page(page)
            page.set_pwd()
            mock_camera.set_password.assert_called_with("newpwd")
            mock_toast.assert_called()
            cancel_all_after(page)


def test_set_pwd_not_locked_set_new(root, mock_camera_manager, mock_camera):
    """Test set_pwd when not locked - set new password"""
    mock_camera.is_locked.return_value = False

    with patch.object(
        SurveillancePage, "_prompt_new_password", return_value="newpwd"
    ):
        with patch("core.pages.surveillance_page.show_toast") as mock_toast:
            page = SurveillancePage(root, "surveillance", mock_camera_manager)
            _setup_page(page)
            page.set_pwd()
            mock_camera.set_password.assert_called_with("newpwd")
            mock_toast.assert_called()
            cancel_all_after(page)


def test_set_pwd_delete(root, mock_camera_manager, mock_camera):
    """Test set_pwd with delete option"""
    mock_camera.is_locked.return_value = False

    with patch.object(
        SurveillancePage, "_prompt_new_password", return_value="DEL"
    ):
        with patch("core.pages.surveillance_page.show_toast") as mock_toast:
            page = SurveillancePage(root, "surveillance", mock_camera_manager)
            _setup_page(page)
            page.set_pwd()
            mock_camera.set_password.assert_called_with(None)
            mock_toast.assert_called()
            cancel_all_after(page)


# =============================================================================
# _prompt_new_password tests
# =============================================================================


def find_dialog(parent):
    """Find CTkToplevel dialog from parent widget."""
    for child in parent.winfo_children():
        if isinstance(child, ctk.CTkToplevel):
            return child
    return None


def find_widgets_by_type(parent, widget_type):
    """Recursively find all widgets of a specific type."""
    result = []
    for child in parent.winfo_children():
        if isinstance(child, widget_type):
            result.append(child)
        result.extend(find_widgets_by_type(child, widget_type))
    return result


def find_button_by_text(parent, text):
    """Find button by its text."""
    buttons = find_widgets_by_type(parent, ctk.CTkButton)
    for btn in buttons:
        if btn.cget("text") == text:
            return btn
    return None


def test_prompt_new_password_dialog(root, mock_camera_manager):
    """Test _prompt_new_password creates dialog and validate_and_close works"""
    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    root.update_idletasks()

    # Start the dialog creation but don't wait
    def mock_wait_window(self, window=None):
        # Find the dialog and buttons
        dialog = find_dialog(page)
        if dialog:
            # Find entry fields and set values
            entries = find_widgets_by_type(dialog, ctk.CTkEntry)
            if len(entries) >= 2:
                entries[0].delete(0, "end")
                entries[0].insert(0, "testpass123")
                entries[1].delete(0, "end")
                entries[1].insert(0, "testpass123")
                root.update_idletasks()
                # Find and click OK button to trigger validate_and_close
                ok_btn = find_button_by_text(dialog, "OK")
                if ok_btn:
                    ok_btn.invoke()
                    root.update_idletasks()

    with patch.object(
        ctk.CTkToplevel, "wait_window", side_effect=mock_wait_window
    ):
        result = page._prompt_new_password()
        assert result == "testpass123"

    cancel_all_after(page)


def test_prompt_new_password_cancel(root, mock_camera_manager):
    """
    Test _prompt_new_password when cancelled - cancel() function is called.
    """
    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    root.update_idletasks()

    def mock_wait_window(self, window=None):
        # Find the dialog and click Cancel button to trigger cancel()
        dialog = find_dialog(page)
        if dialog:
            cancel_btn = find_button_by_text(dialog, "Cancel")
            if cancel_btn:
                cancel_btn.invoke()
                root.update_idletasks()

    with patch.object(
        ctk.CTkToplevel, "wait_window", side_effect=mock_wait_window
    ):
        result = page._prompt_new_password()
        assert result is None

    cancel_all_after(page)


def test_prompt_new_password_delete(root, mock_camera_manager):
    """
    Test _prompt_new_password with delete option - delete() function is called.
    """
    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    root.update_idletasks()

    def mock_wait_window(self, window=None):
        # Find the dialog and click Delete button to trigger delete()
        dialog = find_dialog(page)
        if dialog:
            delete_btn = find_button_by_text(dialog, "Delete password")
            if delete_btn:
                delete_btn.invoke()
                root.update_idletasks()

    with patch.object(
        ctk.CTkToplevel, "wait_window", side_effect=mock_wait_window
    ):
        result = page._prompt_new_password()
        assert result == "DEL"

    cancel_all_after(page)


def test_prompt_new_password_validation_short_password(
    root, mock_camera_manager
):
    """Test validate_and_close with password shorter than 4 characters"""
    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    root.update_idletasks()

    def mock_wait_window(self, window=None):
        dialog = find_dialog(page)
        if dialog:
            entries = find_widgets_by_type(dialog, ctk.CTkEntry)
            if len(entries) >= 2:
                entries[0].delete(0, "end")
                entries[0].insert(0, "abc")  # Too short
                entries[1].delete(0, "end")
                entries[1].insert(0, "abc")
                root.update_idletasks()
                ok_btn = find_button_by_text(dialog, "OK")
                if ok_btn:
                    ok_btn.invoke()
                    root.update_idletasks()
                    # Try again with valid password
                    entries[0].delete(0, "end")
                    entries[0].insert(0, "testpass123")
                    entries[1].delete(0, "end")
                    entries[1].insert(0, "testpass123")
                    root.update_idletasks()
                    ok_btn.invoke()
                    root.update_idletasks()

    with patch.object(
        ctk.CTkToplevel, "wait_window", side_effect=mock_wait_window
    ):
        result = page._prompt_new_password()
        assert result == "testpass123"

    cancel_all_after(page)


def test_prompt_new_password_validation_mismatch(root, mock_camera_manager):
    """Test validate_and_close with mismatched passwords"""
    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    root.update_idletasks()

    def mock_wait_window(self, window=None):
        dialog = find_dialog(page)
        if dialog:
            entries = find_widgets_by_type(dialog, ctk.CTkEntry)
            if len(entries) >= 2:
                entries[0].delete(0, "end")
                entries[0].insert(0, "password1")
                entries[1].delete(0, "end")
                entries[1].insert(0, "password2")  # Mismatch
                root.update_idletasks()
                ok_btn = find_button_by_text(dialog, "OK")
                if ok_btn:
                    ok_btn.invoke()
                    root.update_idletasks()
                    # Try again with matching passwords
                    entries[0].delete(0, "end")
                    entries[0].insert(0, "testpass123")
                    entries[1].delete(0, "end")
                    entries[1].insert(0, "testpass123")
                    root.update_idletasks()
                    ok_btn.invoke()
                    root.update_idletasks()

    with patch.object(
        ctk.CTkToplevel, "wait_window", side_effect=mock_wait_window
    ):
        result = page._prompt_new_password()
        assert result == "testpass123"

    cancel_all_after(page)


def test_prompt_new_password_grab_release_exception(root, mock_camera_manager):
    """Test validate_and_close with grab_release exception"""
    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    root.update_idletasks()

    # Patch CTkToplevel.grab_release to raise an exception
    _ = ctk.CTkToplevel.grab_release

    def failing_grab_release(self):
        raise Exception("Test exception")

    def mock_wait_window(self, window=None):
        dialog = find_dialog(page)
        if dialog:
            entries = find_widgets_by_type(dialog, ctk.CTkEntry)
            if len(entries) >= 2:
                entries[0].delete(0, "end")
                entries[0].insert(0, "testpass123")
                entries[1].delete(0, "end")
                entries[1].insert(0, "testpass123")
                root.update_idletasks()
                ok_btn = find_button_by_text(dialog, "OK")
                if ok_btn:
                    ok_btn.invoke()
                    root.update_idletasks()

    with (
        patch.object(ctk.CTkToplevel, "grab_release", failing_grab_release),
        patch.object(
            ctk.CTkToplevel, "wait_window", side_effect=mock_wait_window
        ),
    ):
        result = page._prompt_new_password()
        assert result == "testpass123"

    cancel_all_after(page)


def test_prompt_new_password_cancel_grab_release_exception(
    root, mock_camera_manager
):
    """Test cancel with grab_release exception"""
    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    root.update_idletasks()

    # Patch CTkToplevel.grab_release to raise an exception
    def failing_grab_release(self):
        raise Exception("Test exception")

    def mock_wait_window(self, window=None):
        dialog = find_dialog(page)
        if dialog:
            cancel_btn = find_button_by_text(dialog, "Cancel")
            if cancel_btn:
                cancel_btn.invoke()
                root.update_idletasks()

    with (
        patch.object(ctk.CTkToplevel, "grab_release", failing_grab_release),
        patch.object(
            ctk.CTkToplevel, "wait_window", side_effect=mock_wait_window
        ),
    ):
        result = page._prompt_new_password()
        assert result is None

    cancel_all_after(page)


# =============================================================================
# _status_item_click_handler tests
# =============================================================================


def test_status_item_click_handler(root, mock_camera_manager):
    page = SurveillancePage(root, "surveillance", mock_camera_manager)

    mock_widget = Mock()
    mock_widget._cam_index = 0
    mock_event = Mock()
    mock_event.widget = mock_widget

    page._status_item_click_handler(mock_event)
    assert page._selected_cam_index == 0
    cancel_all_after(page)


def test_status_item_click_handler_no_index(root, mock_camera_manager):
    page = SurveillancePage(root, "surveillance", mock_camera_manager)

    mock_widget = Mock(spec=[])
    mock_widget.master = None
    mock_event = Mock()
    mock_event.widget = mock_widget

    page._status_item_click_handler(mock_event)
    cancel_all_after(page)


def test_status_item_click_handler_parent_has_index(root, mock_camera_manager):
    page = SurveillancePage(root, "surveillance", mock_camera_manager)

    parent_widget = Mock()
    parent_widget._cam_index = 0

    child_widget = Mock(spec=[])
    child_widget.master = parent_widget

    mock_event = Mock()
    mock_event.widget = child_widget

    page._status_item_click_handler(mock_event)
    assert page._selected_cam_index == 0
    cancel_all_after(page)


# =============================================================================
# _update_controls_and_status tests
# =============================================================================


def test_update_controls_disabled_camera(root, mock_camera_manager):
    mock_camera_manager.get_all_camera_info.return_value = [
        {
            "camera_id": 1,
            "enabled": False,
            "has_password": False,
            "locked": False,
            "coordinate_x": 100,
            "coordinate_y": 100,
        }
    ]
    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    _setup_page(page)
    page._update_controls_and_status()

    assert page.enable_btn.cget("state") == "normal"
    cancel_all_after(page)


def test_update_controls_locked_camera(root, mock_camera_manager):
    mock_camera_manager.get_all_camera_info.return_value = [
        {
            "camera_id": 1,
            "enabled": True,
            "has_password": True,
            "locked": True,
            "coordinate_x": 100,
            "coordinate_y": 100,
        }
    ]
    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    _setup_page(page)
    page._update_controls_and_status()
    cancel_all_after(page)


def test_update_controls_unlocked_camera(root, mock_camera_manager):
    """Test update controls with unlocked camera (not locked)"""
    mock_camera_manager.get_all_camera_info.return_value = [
        {
            "camera_id": 1,
            "enabled": True,
            "has_password": True,
            "locked": False,
            "coordinate_x": 100,
            "coordinate_y": 100,
        }
    ]
    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    _setup_page(page)
    page._update_controls_and_status()
    cancel_all_after(page)


def test_update_controls_no_password(root, mock_camera_manager):
    """Test update controls with no password (pack_forget branch)"""
    mock_camera_manager.get_all_camera_info.return_value = [
        {
            "camera_id": 1,
            "enabled": True,
            "has_password": False,
            "locked": False,
            "coordinate_x": 100,
            "coordinate_y": 100,
        }
    ]
    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    _setup_page(page)
    page._update_controls_and_status()
    cancel_all_after(page)


# =============================================================================
# destroy test
# =============================================================================


def test_destroy(root, mock_camera_manager):
    page = SurveillancePage(root, "surveillance", mock_camera_manager)
    cancel_all_after(page)
    page.destroy()
    mock_camera_manager.update_camera.assert_called()
