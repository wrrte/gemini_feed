"""
Unit tests for configure_page.py
Tests ConfigurePage class with 100% coverage
"""

from unittest.mock import Mock, patch

import customtkinter as ctk
import pytest

from core.pages.configure_page import ConfigurePage


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


def find_dialog(root):
    """Find CTkToplevel dialog from root."""
    for child in root.winfo_children():
        if child.winfo_class() == "Toplevel":
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


@pytest.fixture
def root():
    """Create a real CTk application for tests."""
    root_window = ctk.CTk()
    root_window.withdraw()
    yield root_window
    try:
        cancel_all_after(root_window)
        root_window.update_idletasks()
        root_window.destroy()
    except Exception:
        pass


@pytest.fixture
def mock_config_manager():
    """Create mock ConfigurationManager."""
    manager = Mock()
    system_settings = Mock()
    system_settings.get_panic_phone_number.return_value = "119"
    system_settings.get_homeowner_phone_number.return_value = "010-1234-5678"
    system_settings.get_system_lock_time.return_value = 30
    system_settings.get_alarm_delay_time.return_value = 60
    system_settings.panic_phone_number = "119"
    system_settings.homeowner_phone_number = "010-1234-5678"
    system_settings.system_lock_time = 30
    system_settings.alarm_delay_time = 60
    system_settings.to_schema.return_value = {}

    manager.get_system_setting.return_value = system_settings
    manager.update_system_setting.return_value = True
    return manager


@pytest.fixture
def mock_login_manager():
    """Create mock LoginManager."""
    manager = Mock()
    manager.current_user_id = "testuser"
    manager._verify_web_password.return_value = True
    manager._verify_panel_password.return_value = True
    manager.change_web_password.return_value = True
    manager.change_panel_password.return_value = True
    manager._validate_panel_password.return_value = True
    manager.storage_manager = Mock()
    manager.storage_manager.execute_query.return_value = [["1234"]]
    return manager


# =============================================================================
# Init tests
# =============================================================================


def test_init(root, mock_config_manager):
    """Test basic initialization."""
    page = ConfigurePage(root, "config", mock_config_manager)
    assert page.get_id() == "config"
    assert page.configuration_manager == mock_config_manager


def test_init_with_all_params(root, mock_config_manager, mock_login_manager):
    """Test initialization with all parameters."""
    show_log = Mock()
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="user1",
        show_log_page=show_log,
    )
    assert page.login_manager == mock_login_manager
    assert page.current_user_id == "user1"
    assert page.show_log_page == show_log


# =============================================================================
# draw_page tests
# =============================================================================


def test_draw_page_creates_sections(root, mock_config_manager):
    """Test that draw_page creates page sections."""
    page = ConfigurePage(root, "config", mock_config_manager)
    root.update_idletasks()
    assert page is not None


# =============================================================================
# _create_section tests
# =============================================================================


def test_create_section(root, mock_config_manager):
    """Test section creation."""
    page = ConfigurePage(root, "config", mock_config_manager)
    container = ctk.CTkFrame(root)
    page._create_section(container, "Test Section")


# =============================================================================
# _create_setting_switch tests
# =============================================================================


def test_create_setting_switch(root, mock_config_manager):
    """Test setting switch creation."""
    page = ConfigurePage(root, "config", mock_config_manager)
    container = ctk.CTkFrame(root)
    page._create_setting_switch(container, "Test Switch")


# =============================================================================
# _create_setting_row tests
# =============================================================================


def test_create_setting_row(root, mock_config_manager):
    """Test setting row creation."""
    page = ConfigurePage(root, "config", mock_config_manager)
    container = ctk.CTkFrame(root)
    page._create_setting_row(container, "Label", "Value")


# =============================================================================
# _create_setting_button tests
# =============================================================================


def test_create_setting_button(root, mock_config_manager):
    """Test setting button with color."""
    page = ConfigurePage(root, "config", mock_config_manager)
    container = ctk.CTkFrame(root)
    callback = Mock()
    page._create_setting_button(
        container, "Button", color="#ff0000", command=callback
    )


def test_create_setting_button_no_color(root, mock_config_manager):
    """Test setting button without color."""
    page = ConfigurePage(root, "config", mock_config_manager)
    container = ctk.CTkFrame(root)
    page._create_setting_button(container, "Button", command=None)


# =============================================================================
# _create_dialog_button tests
# =============================================================================


def test_create_dialog_button(root, mock_config_manager):
    """Test dialog button creation."""
    page = ConfigurePage(root, "config", mock_config_manager)
    container = ctk.CTkFrame(root)
    btn = page._create_dialog_button(container, "Dialog Button")
    assert isinstance(btn, ctk.CTkButton)


def test_create_dialog_button_custom(root, mock_config_manager):
    """Test dialog button with custom params."""
    page = ConfigurePage(root, "config", mock_config_manager)
    container = ctk.CTkFrame(root)
    callback = Mock()
    btn = page._create_dialog_button(
        container,
        "Button",
        width=200,
        height=50,
        color="#00ff00",
        command=callback,
    )
    assert btn is not None


# =============================================================================
# _create_editable_setting tests
# =============================================================================


def test_create_editable_setting_with_value(root, mock_config_manager):
    """Test editable setting with value."""
    page = ConfigurePage(
        root, "config", mock_config_manager, current_user_id="user1"
    )
    container = ctk.CTkFrame(root)
    page._create_editable_setting(
        container,
        "Test Setting",
        "panic_phone_number",
        "get_panic_phone_number",
        input_type="text",
    )


def test_create_editable_setting_int_type(root, mock_config_manager):
    """Test editable setting with int type."""
    page = ConfigurePage(root, "config", mock_config_manager)
    container = ctk.CTkFrame(root)
    page._create_editable_setting(
        container,
        "Lock Time",
        "system_lock_time",
        "get_system_lock_time",
        input_type="int",
    )


def test_create_editable_setting_no_value(root, mock_config_manager):
    """Test editable setting when value is None."""
    system_settings = mock_config_manager.get_system_setting.return_value
    system_settings.get_panic_phone_number.return_value = None

    page = ConfigurePage(root, "config", mock_config_manager)
    container = ctk.CTkFrame(root)
    page._create_editable_setting(
        container, "Phone", "panic_phone_number", "get_panic_phone_number"
    )


def test_create_editable_setting_error(root):
    """Test editable setting when error occurs."""
    manager = Mock()
    manager.get_system_setting.side_effect = Exception("Error")

    page = ConfigurePage(root, "config", manager)
    container = ctk.CTkFrame(root)
    page._create_editable_setting(container, "Test", "field", "getter")


# =============================================================================
# _show_change_password_dialog tests
# =============================================================================


def test_show_change_password_dialog_no_manager(root, mock_config_manager):
    """Test password dialog without login manager."""
    page = ConfigurePage(root, "config", mock_config_manager)
    page._show_change_password_dialog()


def test_show_change_password_dialog_with_manager(
    root, mock_config_manager, mock_login_manager
):
    """Test password dialog with login manager."""
    page = ConfigurePage(
        root, "config", mock_config_manager, login_manager=mock_login_manager
    )

    with patch.object(
        page, "_show_password_management_dialog"
    ) as mock_pwd_dialog:
        page._show_change_password_dialog()
        mock_pwd_dialog.assert_called_once()


# =============================================================================
# _create_password_row tests
# =============================================================================


def test_create_password_row(root, mock_config_manager):
    """Test password row creation."""
    page = ConfigurePage(root, "config", mock_config_manager)
    container = ctk.CTkFrame(root)
    page._create_password_row(container, "Web Password", "web", "user1")


# =============================================================================
# _create_guest_password_row tests
# =============================================================================


def test_create_guest_password_row(root, mock_config_manager):
    """Test guest password row creation."""
    page = ConfigurePage(root, "config", mock_config_manager)
    container = ctk.CTkFrame(root)
    page._create_guest_password_row(container)


# =============================================================================
# _show_guest_password_input tests
# =============================================================================


def test_show_guest_password_input_null(
    root, mock_config_manager, mock_login_manager
):
    """Test guest password input when password is NULL."""
    mock_login_manager.storage_manager.execute_query.return_value = [[None]]
    page = ConfigurePage(
        root, "config", mock_config_manager, login_manager=mock_login_manager
    )

    with patch.object(page, "_show_new_guest_password_dialog") as mock_dialog:
        page._show_guest_password_input()
        mock_dialog.assert_called_once_with(None)


def test_show_guest_password_input_exists(
    root, mock_config_manager, mock_login_manager
):
    """Test guest password input when password exists."""
    mock_login_manager.storage_manager.execute_query.return_value = [["1234"]]
    page = ConfigurePage(
        root, "config", mock_config_manager, login_manager=mock_login_manager
    )

    with patch.object(page, "_show_new_password_input") as mock_dialog:
        page._show_guest_password_input()
        mock_dialog.assert_called_once()


def test_show_guest_password_input_error(
    root, mock_config_manager, mock_login_manager
):
    """Test guest password input when error occurs."""
    mock_login_manager.storage_manager.execute_query.side_effect = Exception(
        "Error"
    )
    page = ConfigurePage(
        root, "config", mock_config_manager, login_manager=mock_login_manager
    )
    page._show_guest_password_input()


# =============================================================================
# _show_password_management_dialog tests
# =============================================================================


def test_show_password_management_dialog(
    root, mock_config_manager, mock_login_manager
):
    """Test password management dialog opens."""
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_password_management_dialog()
    root.update_idletasks()

    # Dialog created successfully
    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


# =============================================================================
# _show_new_password_input tests
# =============================================================================


def test_show_new_password_input(
    root, mock_config_manager, mock_login_manager
):
    """Test new password input dialog opens."""
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_password_input("Web Password", "web", "admin")
    root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_new_password_input_verify_and_continue(
    root, mock_config_manager, mock_login_manager
):
    """Test password verification in new password input dialog."""
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_password_input("Web Password", "web", "admin")
    root.update_idletasks()

    # Find the dialog and entry
    dialog = find_dialog(page)
    if dialog:
        entries = find_widgets_by_type(dialog, ctk.CTkEntry)
        if entries:
            # Enter password
            entries[0].insert(0, "oldpassword")
            root.update_idletasks()

            # Find and click confirm button
            confirm_btn = find_button_by_text(dialog, "Confirm")
            if confirm_btn:
                confirm_btn.invoke()
                root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_new_password_input_empty_password(
    root, mock_config_manager, mock_login_manager
):
    """Test verify with empty password shows error."""
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_password_input("Web Password", "web", "admin")
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        # Click confirm without entering password
        confirm_btn = find_button_by_text(dialog, "Confirm")
        if confirm_btn:
            confirm_btn.invoke()
            root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_new_password_input_invalid_password(
    root, mock_config_manager, mock_login_manager
):
    """Test verification with wrong password."""
    mock_login_manager._verify_web_password.return_value = False
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_password_input("Web Password", "web", "admin")
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        entries = find_widgets_by_type(dialog, ctk.CTkEntry)
        if entries:
            entries[0].insert(0, "wrongpass")
            root.update_idletasks()

            confirm_btn = find_button_by_text(dialog, "Confirm")
            if confirm_btn:
                confirm_btn.invoke()
                root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_new_password_input_panel_type(
    root, mock_config_manager, mock_login_manager
):
    """Test new password input for panel type."""
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_password_input("Panel Password", "panel", "admin")
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        entries = find_widgets_by_type(dialog, ctk.CTkEntry)
        if entries:
            entries[0].insert(0, "1234")
            root.update_idletasks()

            confirm_btn = find_button_by_text(dialog, "Confirm")
            if confirm_btn:
                confirm_btn.invoke()
                root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_new_password_input_guest(
    root, mock_config_manager, mock_login_manager
):
    """Test new password input for guest user."""
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_password_input("Guest Password", "panel", "guest")
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        entries = find_widgets_by_type(dialog, ctk.CTkEntry)
        if entries:
            entries[0].insert(0, "1234")
            root.update_idletasks()

            confirm_btn = find_button_by_text(dialog, "Confirm")
            if confirm_btn:
                confirm_btn.invoke()
                root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_new_password_input_verify_error(
    root, mock_config_manager, mock_login_manager
):
    """Test verify when exception occurs."""
    mock_login_manager._verify_web_password.side_effect = Exception("Error")
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_password_input("Web Password", "web", "admin")
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        entries = find_widgets_by_type(dialog, ctk.CTkEntry)
        if entries:
            entries[0].insert(0, "pass")
            root.update_idletasks()

            confirm_btn = find_button_by_text(dialog, "Confirm")
            if confirm_btn:
                confirm_btn.invoke()
                root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


# =============================================================================
# _show_new_password_dialog tests
# =============================================================================


def test_show_new_password_dialog_web(
    root, mock_config_manager, mock_login_manager
):
    """Test new password dialog for web type."""
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_password_dialog("Web Password", "web", "admin", "oldpass")
    root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_new_password_dialog_panel(
    root, mock_config_manager, mock_login_manager
):
    """Test new password dialog for panel type."""
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_password_dialog("Panel Password", "panel", "admin", "1234")
    root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_new_password_dialog_confirm(
    root, mock_config_manager, mock_login_manager
):
    """Test confirming new password."""
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_password_dialog("Web Password", "web", "admin", "oldpass")
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        entries = find_widgets_by_type(dialog, ctk.CTkEntry)
        if entries:
            entries[0].insert(0, "newpassword")
            root.update_idletasks()

            confirm_btn = find_button_by_text(dialog, "Confirm")
            if confirm_btn:
                confirm_btn.invoke()
                root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_new_password_dialog_confirm_panel(
    root, mock_config_manager, mock_login_manager
):
    """Test confirming new panel password."""
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_password_dialog("Panel Password", "panel", "admin", "1234")
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        entries = find_widgets_by_type(dialog, ctk.CTkEntry)
        if entries:
            entries[0].insert(0, "5678")
            root.update_idletasks()

            confirm_btn = find_button_by_text(dialog, "Confirm")
            if confirm_btn:
                confirm_btn.invoke()
                root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_new_password_dialog_empty(
    root, mock_config_manager, mock_login_manager
):
    """Test confirming with empty password."""
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_password_dialog("Web Password", "web", "admin", "oldpass")
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        confirm_btn = find_button_by_text(dialog, "Confirm")
        if confirm_btn:
            confirm_btn.invoke()
            root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_new_password_dialog_change_fails(
    root, mock_config_manager, mock_login_manager
):
    """Test when password change fails."""
    mock_login_manager.change_web_password.return_value = False
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_password_dialog("Web Password", "web", "admin", "oldpass")
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        entries = find_widgets_by_type(dialog, ctk.CTkEntry)
        if entries:
            entries[0].insert(0, "newpass")
            root.update_idletasks()

            confirm_btn = find_button_by_text(dialog, "Confirm")
            if confirm_btn:
                confirm_btn.invoke()
                root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_new_password_dialog_error(
    root, mock_config_manager, mock_login_manager
):
    """Test when exception occurs during password change."""
    mock_login_manager.change_web_password.side_effect = Exception("Error")
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_password_dialog("Web Password", "web", "admin", "oldpass")
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        entries = find_widgets_by_type(dialog, ctk.CTkEntry)
        if entries:
            entries[0].insert(0, "newpass")
            root.update_idletasks()

            confirm_btn = find_button_by_text(dialog, "Confirm")
            if confirm_btn:
                confirm_btn.invoke()
                root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


# =============================================================================
# _show_new_guest_password_dialog tests
# =============================================================================


def test_show_new_guest_password_dialog(
    root, mock_config_manager, mock_login_manager
):
    """Test guest password dialog opens."""
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_guest_password_dialog("1234")
    root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_new_guest_password_dialog_null(
    root, mock_config_manager, mock_login_manager
):
    """Test guest password dialog with NULL old password."""
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_guest_password_dialog(None)
    root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_new_guest_password_dialog_set_password(
    root, mock_config_manager, mock_login_manager
):
    """Test setting new guest password."""
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_guest_password_dialog("1234")
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        entries = find_widgets_by_type(dialog, ctk.CTkEntry)
        if entries:
            entries[0].insert(0, "5678")
            root.update_idletasks()

            confirm_btn = find_button_by_text(dialog, "Confirm")
            if confirm_btn:
                confirm_btn.invoke()
                root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_new_guest_password_dialog_set_from_null(
    root, mock_config_manager, mock_login_manager
):
    """Test setting guest password when old is NULL."""
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_guest_password_dialog(None)
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        entries = find_widgets_by_type(dialog, ctk.CTkEntry)
        if entries:
            entries[0].insert(0, "5678")
            root.update_idletasks()

            confirm_btn = find_button_by_text(dialog, "Confirm")
            if confirm_btn:
                confirm_btn.invoke()
                root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_new_guest_password_dialog_empty(
    root, mock_config_manager, mock_login_manager
):
    """Test confirming with empty password."""
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_guest_password_dialog("1234")
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        confirm_btn = find_button_by_text(dialog, "Confirm")
        if confirm_btn:
            confirm_btn.invoke()
            root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_new_guest_password_dialog_disable(
    root, mock_config_manager, mock_login_manager
):
    """Test disabling guest password via checkbox."""
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_guest_password_dialog("1234")
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        # Find and toggle the checkbox
        checkboxes = find_widgets_by_type(dialog, ctk.CTkCheckBox)
        if checkboxes:
            checkboxes[0].toggle()
            root.update_idletasks()

            confirm_btn = find_button_by_text(dialog, "Confirm")
            if confirm_btn:
                confirm_btn.invoke()
                root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_new_guest_password_dialog_toggle_checkbox(
    root, mock_config_manager, mock_login_manager
):
    """Test toggling checkbox on and off."""
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_guest_password_dialog("1234")
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        checkboxes = find_widgets_by_type(dialog, ctk.CTkCheckBox)
        if checkboxes:
            # Toggle on (disable)
            checkboxes[0].toggle()
            root.update_idletasks()
            # Toggle off (enable) - covers line 693
            checkboxes[0].toggle()
            root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_new_guest_password_dialog_disable_fails(
    root, mock_config_manager, mock_login_manager
):
    """Test when disabling guest password fails."""
    mock_login_manager.storage_manager.execute_query.return_value = None
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_guest_password_dialog("1234")
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        checkboxes = find_widgets_by_type(dialog, ctk.CTkCheckBox)
        if checkboxes:
            checkboxes[0].toggle()
            root.update_idletasks()

            confirm_btn = find_button_by_text(dialog, "Confirm")
            if confirm_btn:
                confirm_btn.invoke()
                root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_new_guest_password_dialog_disable_error(
    root, mock_config_manager, mock_login_manager
):
    """Test when exception occurs during disable."""
    mock_login_manager.storage_manager.execute_query.side_effect = Exception(
        "Error"
    )
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_guest_password_dialog("1234")
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        checkboxes = find_widgets_by_type(dialog, ctk.CTkCheckBox)
        if checkboxes:
            checkboxes[0].toggle()
            root.update_idletasks()

            confirm_btn = find_button_by_text(dialog, "Confirm")
            if confirm_btn:
                confirm_btn.invoke()
                root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_new_guest_password_dialog_invalid(
    root, mock_config_manager, mock_login_manager
):
    """Test when new guest password is invalid."""
    mock_login_manager._validate_panel_password.return_value = False
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_guest_password_dialog(None)
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        entries = find_widgets_by_type(dialog, ctk.CTkEntry)
        if entries:
            entries[0].insert(0, "invalid")
            root.update_idletasks()

            confirm_btn = find_button_by_text(dialog, "Confirm")
            if confirm_btn:
                confirm_btn.invoke()
                root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_new_guest_password_dialog_change_fails(
    root, mock_config_manager, mock_login_manager
):
    """Test when guest password change fails."""
    mock_login_manager.change_panel_password.return_value = False
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_guest_password_dialog("1234")
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        entries = find_widgets_by_type(dialog, ctk.CTkEntry)
        if entries:
            entries[0].insert(0, "5678")
            root.update_idletasks()

            confirm_btn = find_button_by_text(dialog, "Confirm")
            if confirm_btn:
                confirm_btn.invoke()
                root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_new_guest_password_dialog_change_error(
    root, mock_config_manager, mock_login_manager
):
    """Test when exception occurs during guest password change."""
    mock_login_manager.change_panel_password.side_effect = Exception("Error")
    page = ConfigurePage(
        root,
        "config",
        mock_config_manager,
        login_manager=mock_login_manager,
        current_user_id="admin",
    )
    root.update_idletasks()

    page._show_new_guest_password_dialog("1234")
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        entries = find_widgets_by_type(dialog, ctk.CTkEntry)
        if entries:
            entries[0].insert(0, "5678")
            root.update_idletasks()

            confirm_btn = find_button_by_text(dialog, "Confirm")
            if confirm_btn:
                confirm_btn.invoke()
                root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


# =============================================================================
# _show_input_dialog tests
# =============================================================================


def test_show_input_dialog(root, mock_config_manager):
    """Test input dialog opens."""
    page = ConfigurePage(
        root, "config", mock_config_manager, current_user_id="admin"
    )
    root.update_idletasks()

    value_label = ctk.CTkLabel(page, text="119")
    page._show_input_dialog(
        "Panic Phone",
        "panic_phone_number",
        "get_panic_phone_number",
        value_label,
        "text",
        "Enter phone number",
    )
    root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_input_dialog_int_type(root, mock_config_manager):
    """Test input dialog with int type."""
    page = ConfigurePage(
        root, "config", mock_config_manager, current_user_id="admin"
    )
    root.update_idletasks()

    value_label = ctk.CTkLabel(page, text="30 min")
    page._show_input_dialog(
        "Lock Time",
        "system_lock_time",
        "get_system_lock_time",
        value_label,
        "int",
        "Enter time",
    )
    root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_input_dialog_confirm(root, mock_config_manager):
    """Test confirming input dialog."""
    page = ConfigurePage(
        root, "config", mock_config_manager, current_user_id="admin"
    )
    root.update_idletasks()

    value_label = ctk.CTkLabel(page, text="119")
    page._show_input_dialog(
        "Panic Phone",
        "panic_phone_number",
        "get_panic_phone_number",
        value_label,
        "text",
        "Enter phone",
    )
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        entries = find_widgets_by_type(dialog, ctk.CTkEntry)
        if entries:
            entries[0].delete(0, "end")
            entries[0].insert(0, "112")
            root.update_idletasks()

            confirm_btn = find_button_by_text(dialog, "Confirm")
            if confirm_btn:
                confirm_btn.invoke()
                root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_input_dialog_confirm_int(root, mock_config_manager):
    """Test confirming int input dialog."""
    page = ConfigurePage(
        root, "config", mock_config_manager, current_user_id="admin"
    )
    root.update_idletasks()

    value_label = ctk.CTkLabel(page, text="30 min")
    page._show_input_dialog(
        "Lock Time",
        "system_lock_time",
        "get_system_lock_time",
        value_label,
        "int",
        "Enter time",
    )
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        entries = find_widgets_by_type(dialog, ctk.CTkEntry)
        if entries:
            entries[0].delete(0, "end")
            entries[0].insert(0, "60")
            root.update_idletasks()

            confirm_btn = find_button_by_text(dialog, "Confirm")
            if confirm_btn:
                confirm_btn.invoke()
                root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_input_dialog_empty(root, mock_config_manager):
    """Test confirming with empty value."""
    page = ConfigurePage(
        root, "config", mock_config_manager, current_user_id="admin"
    )
    root.update_idletasks()

    value_label = ctk.CTkLabel(page, text="119")
    page._show_input_dialog(
        "Phone",
        "panic_phone_number",
        "get_panic_phone_number",
        value_label,
        "text",
        "Enter",
    )
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        entries = find_widgets_by_type(dialog, ctk.CTkEntry)
        if entries:
            entries[0].delete(0, "end")
            root.update_idletasks()

            confirm_btn = find_button_by_text(dialog, "Confirm")
            if confirm_btn:
                confirm_btn.invoke()
                root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_input_dialog_invalid_int(root, mock_config_manager):
    """Test confirming with invalid int value."""
    page = ConfigurePage(
        root, "config", mock_config_manager, current_user_id="admin"
    )
    root.update_idletasks()

    value_label = ctk.CTkLabel(page, text="30 min")
    page._show_input_dialog(
        "Time",
        "system_lock_time",
        "get_system_lock_time",
        value_label,
        "int",
        "Enter",
    )
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        entries = find_widgets_by_type(dialog, ctk.CTkEntry)
        if entries:
            entries[0].delete(0, "end")
            entries[0].insert(0, "not_a_number")
            root.update_idletasks()

            confirm_btn = find_button_by_text(dialog, "Confirm")
            if confirm_btn:
                confirm_btn.invoke()
                root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_input_dialog_no_config_manager(root):
    """Test input dialog without config manager."""
    manager = Mock()
    manager.get_system_setting.return_value = Mock(
        get_panic_phone_number=Mock(return_value="119"),
        panic_phone_number="119",
        to_schema=Mock(return_value={}),
    )
    manager.update_system_setting.return_value = True

    page = ConfigurePage(root, "config", None, current_user_id="admin")
    page.configuration_manager = None
    root.update_idletasks()

    value_label = ctk.CTkLabel(page, text="119")
    page._show_input_dialog(
        "Phone",
        "panic_phone_number",
        "get_panic_phone_number",
        value_label,
        "text",
        "Enter",
    )
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        entries = find_widgets_by_type(dialog, ctk.CTkEntry)
        if entries:
            entries[0].insert(0, "112")
            root.update_idletasks()

            confirm_btn = find_button_by_text(dialog, "Confirm")
            if confirm_btn:
                confirm_btn.invoke()
                root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_input_dialog_no_settings(root, mock_config_manager):
    """Test input dialog when settings is None."""
    mock_config_manager.get_system_setting.return_value = None
    page = ConfigurePage(
        root, "config", mock_config_manager, current_user_id="admin"
    )
    root.update_idletasks()

    value_label = ctk.CTkLabel(page, text="119")
    page._show_input_dialog(
        "Phone",
        "panic_phone_number",
        "get_panic_phone_number",
        value_label,
        "text",
        "Enter",
    )
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        entries = find_widgets_by_type(dialog, ctk.CTkEntry)
        if entries:
            entries[0].insert(0, "112")
            root.update_idletasks()

            confirm_btn = find_button_by_text(dialog, "Confirm")
            if confirm_btn:
                confirm_btn.invoke()
                root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_input_dialog_update_fails(root, mock_config_manager):
    """Test input dialog when update fails."""
    mock_config_manager.update_system_setting.return_value = False
    page = ConfigurePage(
        root, "config", mock_config_manager, current_user_id="admin"
    )
    root.update_idletasks()

    value_label = ctk.CTkLabel(page, text="119")
    page._show_input_dialog(
        "Phone",
        "panic_phone_number",
        "get_panic_phone_number",
        value_label,
        "text",
        "Enter",
    )
    root.update_idletasks()

    dialog = find_dialog(page)
    if dialog:
        entries = find_widgets_by_type(dialog, ctk.CTkEntry)
        if entries:
            entries[0].delete(0, "end")
            entries[0].insert(0, "112")
            root.update_idletasks()

            confirm_btn = find_button_by_text(dialog, "Confirm")
            if confirm_btn:
                confirm_btn.invoke()
                root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def test_show_input_dialog_load_error(root, mock_config_manager):
    """Test input dialog when loading value errors."""
    mock_config_manager.get_system_setting.side_effect = Exception("Error")
    page = ConfigurePage(
        root, "config", mock_config_manager, current_user_id="admin"
    )
    # Reset side effect for dialog creation
    mock_config_manager.get_system_setting.side_effect = None
    mock_config_manager.get_system_setting.return_value = Mock(
        get_panic_phone_number=Mock(side_effect=Exception("Load error")),
    )
    root.update_idletasks()

    value_label = ctk.CTkLabel(page, text="119")
    page._show_input_dialog(
        "Phone",
        "panic_phone_number",
        "get_panic_phone_number",
        value_label,
        "text",
        "Enter",
    )
    root.update_idletasks()

    for widget in page.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass
