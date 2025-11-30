"""
Unit tests for web_app.py
Tests WebApp class with 100% coverage
"""

from unittest.mock import Mock, patch

import customtkinter as ctk
import pytest

from core.pages.interface_page import InterfacePage, InterfaceWindow
from core.pages.login_page import LoginPage
from core.web_app import WebApp


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
    root_window.update_idletasks()
    yield root_window
    try:
        cancel_all_after(root_window)
        root_window.update_idletasks()
        root_window.destroy()
        root_window.update_idletasks()
    except Exception:
        pass


@pytest.fixture
def mock_master():
    """Create a mock master (ControlPanel) with powered attribute."""
    master = Mock()
    master.powered = True
    return master


@pytest.fixture
def mock_login_manager():
    """Create a mock login manager."""
    manager = Mock()
    manager.is_logged_in_web = False
    manager.current_user_id = "testuser"
    return manager


@pytest.fixture
def mock_sensor_manager():
    """Create a mock sensor manager."""
    return Mock()


@pytest.fixture
def mock_camera_manager():
    """Create a mock camera manager."""
    return Mock()


@pytest.fixture
def mock_configuration_manager():
    """Create a mock configuration manager."""
    return Mock()


@pytest.fixture(autouse=True)
def ensure_tkinter_cleanup():
    """Ensure Tkinter is properly cleaned up between tests."""
    yield
    try:
        import tkinter

        if hasattr(tkinter, "_default_root") and tkinter._default_root:
            try:
                for widget in list(tkinter._default_root.winfo_children()):
                    try:
                        if isinstance(
                            widget,
                            (tkinter.Toplevel, ctk.CTkToplevel, ctk.CTk),
                        ):
                            widget.withdraw()
                            widget.destroy()
                    except Exception:
                        pass
            except Exception:
                pass

            if tkinter._default_root.winfo_exists():
                cancel_all_after(tkinter._default_root)
                tkinter._default_root.update_idletasks()
                tkinter._default_root.destroy()
                tkinter._default_root.update_idletasks()
            tkinter._default_root = None
    except Exception:
        pass


@pytest.fixture(autouse=True)
def mock_show_toast():
    """Mock show_toast to prevent actual toast display."""
    with patch("core.web_app.show_toast"):
        yield


@pytest.fixture(autouse=True)
def mock_page_classes():
    """Mock page classes to prevent actual page creation during init."""
    with (
        patch("core.web_app.SecurityPage"),
        patch("core.web_app.SafeHomeModePage"),
        patch("core.web_app.SurveillancePage"),
        patch("core.web_app.MultiCameraViewPage"),
        patch("core.web_app.ViewLogPage"),
        patch("core.web_app.ConfigurePage"),
        patch("core.web_app.SensorsManagementPage"),
    ):
        yield


# =============================================================================
# Init tests
# =============================================================================


def test_init_without_login(
    root, mock_login_manager, mock_sensor_manager, mock_camera_manager
):
    """Test WebApp initialization without login."""
    with patch.object(WebApp, "draw_page") as mock_draw:
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=mock_camera_manager,
        )

        assert app.login_manager == mock_login_manager
        assert app.sensor_manager == mock_sensor_manager
        assert app.camera_manager == mock_camera_manager
        assert app.configuration_manager is None
        assert app.navbar is None
        assert app.content is None
        assert app.pages == {}
        assert app.single_camera_views == {}
        assert app.container is not None
        mock_draw.assert_called_once()


def test_init_with_login(
    root,
    mock_login_manager,
    mock_sensor_manager,
    mock_camera_manager,
    mock_configuration_manager,
):
    """Test WebApp initialization with logged in user."""
    mock_login_manager.is_logged_in_web = True

    with patch.object(WebApp, "draw_page") as mock_draw:
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=mock_camera_manager,
            configuration_manager=mock_configuration_manager,
        )

        assert app.configuration_manager == mock_configuration_manager
        mock_draw.assert_called_once()


def test_init_with_custom_params(
    root, mock_login_manager, mock_sensor_manager
):
    """Test WebApp initialization with custom page_id and title."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
            page_id="CustomApp",
            title="Custom Title",
        )

        assert app.get_id() == "CustomApp"
        assert app.title() == "Custom Title"


# =============================================================================
# draw_page tests
# =============================================================================


def test_draw_page_not_logged_in(
    root, mock_login_manager, mock_sensor_manager
):
    """Test draw_page when user is not logged in."""
    mock_login_manager.is_logged_in_web = False

    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

    # Now test draw_page without patching it
    with patch.object(app, "draw_login_page") as mock_draw_login:
        app.draw_page()
        mock_draw_login.assert_called_once()


def test_draw_page_logged_in(root, mock_login_manager, mock_sensor_manager):
    """Test draw_page when user is logged in."""
    mock_login_manager.is_logged_in_web = True

    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

    # Now test draw_page without patching it
    with patch.object(app, "draw_main_interface") as mock_draw_main:
        app.draw_page()
        mock_draw_main.assert_called_once()


def test_draw_page_no_login_manager(root, mock_sensor_manager):
    """Test draw_page when login_manager is None."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=None,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

    # Now test draw_page without patching it
    with patch.object(app, "draw_login_page") as mock_draw_login:
        app.draw_page()
        mock_draw_login.assert_called_once()


# =============================================================================
# is_system_powered tests
# =============================================================================


def test_is_system_powered_true(root, mock_login_manager):
    """Test is_system_powered returns True when master has powered=True."""
    # Create a real CTk instance with powered attribute
    master = ctk.CTk()
    master.powered = True
    master.withdraw()

    try:
        with patch.object(WebApp, "draw_page"):
            app = WebApp(
                master,
                login_manager=mock_login_manager,
                sensor_manager=Mock(),
                camera_manager=Mock(),
            )
            assert app.is_system_powered() is True
    finally:
        try:
            master.destroy()
        except Exception:
            pass


def test_is_system_powered_false(root, mock_login_manager):
    """Test is_system_powered returns False when master has no powered attr."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=Mock(),
            camera_manager=Mock(),
        )
        assert app.is_system_powered() is False


def test_is_system_powered_false_when_powered_false(root, mock_login_manager):
    """Test is_system_powered returns False when master.powered=False."""
    # Create a real CTk instance with powered=False
    master = ctk.CTk()
    master.powered = False
    master.withdraw()

    try:
        with patch.object(WebApp, "draw_page"):
            app = WebApp(
                master,
                login_manager=mock_login_manager,
                sensor_manager=Mock(),
                camera_manager=Mock(),
            )
            assert app.is_system_powered() is False
    finally:
        try:
            master.destroy()
        except Exception:
            pass


# =============================================================================
# draw_login_page tests
# =============================================================================


def test_draw_login_page_creates_new(
    root, mock_login_manager, mock_sensor_manager
):
    """Test draw_login_page creates new login page if not exists."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        with patch.object(app, "close_all_single_camera_views") as mock_close:
            with patch.object(app, "destroy_page"):
                with patch.object(app, "register_page") as mock_register:
                    with patch.object(app, "show_page") as mock_show:
                        app.draw_login_page()

                        mock_close.assert_called_once()
                        mock_register.assert_called_once()
                        mock_show.assert_called_once_with(LoginPage.__name__)


def test_draw_login_page_reuses_existing(
    root, mock_login_manager, mock_sensor_manager
):
    """Test draw_login_page reuses existing login page."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        # Create a mock login page
        mock_login_page = Mock()
        app.pages[LoginPage.__name__] = mock_login_page

        with patch.object(app, "close_all_single_camera_views"):
            with patch.object(app, "destroy_page"):
                with patch.object(app, "register_page") as mock_register:
                    with patch.object(app, "show_page") as mock_show:
                        app.draw_login_page()

                        # Should not register again
                        mock_register.assert_not_called()
                        mock_show.assert_called_once_with(LoginPage.__name__)


def test_draw_login_page_destroys_other_pages(
    root, mock_login_manager, mock_sensor_manager
):
    """Test draw_login_page destroys all pages except login page."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        # Add some other pages
        app.pages["SecurityPage"] = Mock()
        app.pages["SurveillancePage"] = Mock()
        app.pages[LoginPage.__name__] = Mock()

        with patch.object(app, "close_all_single_camera_views"):
            with patch.object(app, "destroy_page") as mock_destroy:
                with patch.object(app, "show_page"):
                    app.draw_login_page()

                    # Should destroy other pages but not login page
                    assert mock_destroy.call_count == 2
                    assert (
                        mock_destroy.call_args_list[0][0][0] == "SecurityPage"
                    )
                    assert (
                        mock_destroy.call_args_list[1][0][0]
                        == "SurveillancePage"
                    )


# =============================================================================
# draw_main_interface tests
# =============================================================================


def test_draw_main_interface(root, mock_login_manager, mock_sensor_manager):
    """Test draw_main_interface initializes main interface."""
    mock_login_manager.is_logged_in_web = True

    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        # Add some pages
        app.pages["SecurityPage"] = Mock()
        app.pages["SurveillancePage"] = Mock()

        with patch.object(app, "hide_page") as mock_hide:
            with patch.object(app, "init_main_interface") as mock_init:
                with patch.object(app, "show_page") as mock_show:
                    app.draw_main_interface()

                    # Should hide all pages
                    assert mock_hide.call_count == 2
                    mock_init.assert_called_once()
                    mock_show.assert_called_once_with("SecurityPage")


# =============================================================================
# switch_to_main tests
# =============================================================================


def test_switch_to_main_system_powered(
    root, mock_login_manager, mock_sensor_manager
):
    """Test switch_to_main when system is powered."""
    # Create a real CTk instance with powered=True
    master = ctk.CTk()
    master.powered = True
    master.withdraw()

    try:
        with patch.object(WebApp, "draw_page"):
            app = WebApp(
                master,
                login_manager=mock_login_manager,
                sensor_manager=mock_sensor_manager,
                camera_manager=Mock(),
            )

            with patch.object(app, "draw_page") as mock_draw:
                with patch.object(app, "show_page") as mock_show:
                    app.switch_to_main()

                    mock_draw.assert_called_once()
                    mock_show.assert_called_once_with("SecurityPage")
    finally:
        try:
            master.destroy()
        except Exception:
            pass


def test_switch_to_main_system_not_powered(
    root, mock_login_manager, mock_sensor_manager
):
    """Test switch_to_main when system is not powered."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        with patch("core.web_app.show_toast") as mock_toast:
            with patch.object(app, "draw_page") as mock_draw:
                with patch.object(app, "show_page") as mock_show:
                    app.switch_to_main()

                    mock_toast.assert_called_once_with(
                        app, "Control Panel is not powered"
                    )
                    mock_draw.assert_not_called()
                    mock_show.assert_not_called()


# =============================================================================
# register_page tests
# =============================================================================


def test_register_page_interface_window(
    root, mock_login_manager, mock_sensor_manager
):
    """Test register_page with InterfaceWindow subclass."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        class TestWindow(InterfaceWindow):
            def draw_page(self):
                pass

        with patch.object(app, "content"):
            app.register_page(TestWindow)

            assert "TestWindow" in app.pages
            page = app.pages["TestWindow"]
            assert isinstance(page, InterfaceWindow)
            assert page.master == app


def test_register_page_interface_window_with_master(
    root, mock_login_manager, mock_sensor_manager
):
    """Test register_page with InterfaceWindow and custom master."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        custom_master = ctk.CTk()
        custom_master.withdraw()

        try:

            class TestWindow(InterfaceWindow):
                def draw_page(self):
                    pass

            app.register_page(TestWindow, master=custom_master)

            assert "TestWindow" in app.pages
            page = app.pages["TestWindow"]
            assert page.master == custom_master
        finally:
            try:
                custom_master.destroy()
            except Exception:
                pass


def test_register_page_interface_page(
    root, mock_login_manager, mock_sensor_manager
):
    """Test register_page with InterfacePage subclass."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        # Initialize content frame
        app.content = ctk.CTkFrame(app)

        class TestPage(InterfacePage):
            def draw_page(self):
                pass

        app.register_page(TestPage)

        assert "TestPage" in app.pages
        page = app.pages["TestPage"]
        assert isinstance(page, InterfacePage)
        assert page.master == app.content


def test_register_page_interface_page_with_master(
    root, mock_login_manager, mock_sensor_manager
):
    """Test register_page with InterfacePage and custom master."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        custom_master = ctk.CTkFrame(app)

        class TestPage(InterfacePage):
            def draw_page(self):
                pass

        app.register_page(TestPage, master=custom_master)

        assert "TestPage" in app.pages
        page = app.pages["TestPage"]
        assert page.master == custom_master


def test_register_page_ctkframe(root, mock_login_manager, mock_sensor_manager):
    """Test register_page with CTkFrame subclass."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        app.content = ctk.CTkFrame(app)

        class TestFrame(ctk.CTkFrame):
            pass

        app.register_page(TestFrame)

        assert "TestFrame" in app.pages
        page = app.pages["TestFrame"]
        assert isinstance(page, ctk.CTkFrame)
        assert page.master == app.content


def test_register_page_unknown_type(
    root, mock_login_manager, mock_sensor_manager
):
    """Test register_page with unknown page type."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        class UnknownPage:
            pass

        with patch("builtins.print") as mock_print:
            app.register_page(UnknownPage)

            mock_print.assert_called_once()
            assert "Error: Unknown page type" in mock_print.call_args[0][0]


# =============================================================================
# show_page tests
# =============================================================================


def test_show_page_not_found(root, mock_login_manager, mock_sensor_manager):
    """Test show_page when page is not found."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        with patch("builtins.print") as mock_print:
            app.show_page("NonExistentPage")

            mock_print.assert_called_once_with(
                "Page 'NonExistentPage' not found."
            )


def test_show_page_interface_window(
    root, mock_login_manager, mock_sensor_manager
):
    """Test show_page with InterfaceWindow."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        mock_window = Mock(spec=InterfaceWindow)
        mock_window.deiconify = Mock()
        mock_window.focus = Mock()
        app.pages["TestWindow"] = mock_window

        app.show_page("TestWindow")

        mock_window.deiconify.assert_called_once()
        mock_window.focus.assert_called_once()


def test_show_page_interface_page(
    root, mock_login_manager, mock_sensor_manager
):
    """Test show_page with InterfacePage."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        mock_page = Mock(spec=InterfacePage)
        mock_page.place = Mock()
        mock_page.tkraise = Mock()
        app.pages["TestPage"] = mock_page

        app.show_page("TestPage")

        mock_page.place.assert_called_once_with(
            relx=0, rely=0, relwidth=1.0, relheight=1.0
        )
        mock_page.tkraise.assert_called_once()


def test_show_page_other_type(root, mock_login_manager, mock_sensor_manager):
    """Test show_page with other CTkFrame-based widget."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        mock_frame = Mock(spec=ctk.CTkFrame)
        mock_frame.place = Mock()
        mock_frame.tkraise = Mock()
        app.pages["TestFrame"] = mock_frame

        app.show_page("TestFrame")

        mock_frame.place.assert_called_once_with(
            relx=0, rely=0, relwidth=1.0, relheight=1.0
        )
        mock_frame.tkraise.assert_called_once()


# =============================================================================
# hide_page tests
# =============================================================================


def test_hide_page_not_found(root, mock_login_manager, mock_sensor_manager):
    """Test hide_page when page is not found."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        with patch("builtins.print") as mock_print:
            app.hide_page("NonExistentPage")

            mock_print.assert_called_once_with(
                "Page 'NonExistentPage' not found."
            )


def test_hide_page_interface_window(
    root, mock_login_manager, mock_sensor_manager
):
    """Test hide_page with InterfaceWindow."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        mock_window = Mock(spec=InterfaceWindow)
        mock_window.withdraw = Mock()
        app.pages["TestWindow"] = mock_window

        app.hide_page("TestWindow")

        mock_window.withdraw.assert_called_once()


def test_hide_page_interface_page(
    root, mock_login_manager, mock_sensor_manager
):
    """Test hide_page with InterfacePage."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        mock_page = Mock(spec=InterfacePage)
        mock_page.place_forget = Mock()
        app.pages["TestPage"] = mock_page

        app.hide_page("TestPage")

        mock_page.place_forget.assert_called_once()


def test_hide_page_other_type(root, mock_login_manager, mock_sensor_manager):
    """Test hide_page with other CTkFrame-based widget."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        mock_frame = Mock(spec=ctk.CTkFrame)
        mock_frame.place_forget = Mock()
        app.pages["TestFrame"] = mock_frame

        app.hide_page("TestFrame")

        mock_frame.place_forget.assert_called_once()


# =============================================================================
# destroy_page tests
# =============================================================================


def test_destroy_page_not_found(root, mock_login_manager, mock_sensor_manager):
    """Test destroy_page when page is not found."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        with patch("builtins.print") as mock_print:
            app.destroy_page("NonExistentPage")

            mock_print.assert_called_once_with(
                "Page 'NonExistentPage' not found."
            )


def test_destroy_page_success(root, mock_login_manager, mock_sensor_manager):
    """Test destroy_page successfully destroys page."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        mock_page = Mock()
        mock_page.destroy = Mock()
        app.pages["TestPage"] = mock_page

        app.destroy_page("TestPage")

        mock_page.destroy.assert_called_once()
        assert "TestPage" not in app.pages


def test_destroy_page_exception(root, mock_login_manager, mock_sensor_manager):
    """Test destroy_page handles exception during destroy."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        mock_page = Mock()
        mock_page.destroy.side_effect = Exception("Destroy failed")
        app.pages["TestPage"] = mock_page

        with patch("builtins.print") as mock_print:
            app.destroy_page("TestPage")

            mock_print.assert_called_once()
            assert "Failed to destroy page" in mock_print.call_args[0][0]
            assert "TestPage" not in app.pages  # Should still be removed


# =============================================================================
# init_main_interface tests
# =============================================================================


def test_init_main_interface_creates_navbar_and_content(
    root, mock_login_manager, mock_sensor_manager, mock_camera_manager
):
    """Test init_main_interface creates navbar and content frames."""
    mock_login_manager.is_logged_in_web = True

    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=mock_camera_manager,
        )

        with patch.object(app, "register_page") as mock_register:
            app.init_main_interface()

            assert app.navbar is not None
            assert app.content is not None
            assert isinstance(app.navbar, ctk.CTkFrame)
            assert isinstance(app.content, ctk.CTkFrame)
            # Should register all pages
            assert mock_register.call_count >= 6


def test_init_main_interface_registers_pages(
    root, mock_login_manager, mock_sensor_manager, mock_camera_manager
):
    """Test init_main_interface registers all required pages."""
    mock_login_manager.is_logged_in_web = True

    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=mock_camera_manager,
        )

        with patch.object(app, "register_page") as mock_register:
            app.init_main_interface()

            # Check that register_page was called for all pages
            # Get the class names from the call arguments
            registered_names = []
            for call in mock_register.call_args_list:
                page_class = call[0][0]
                # Handle both real classes and mocks
                if hasattr(page_class, "__name__"):
                    registered_names.append(page_class.__name__)
                else:
                    # For mocked classes, check the call args
                    registered_names.append(str(page_class))

            # Verify register_page was called 7 times (for 7 pages)
            assert mock_register.call_count == 7


def test_init_main_interface_creates_nav_buttons(
    root, mock_login_manager, mock_sensor_manager, mock_camera_manager
):
    """Test init_main_interface creates navigation buttons."""
    mock_login_manager.is_logged_in_web = True

    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=mock_camera_manager,
        )

        with patch.object(app, "register_page"):
            app.init_main_interface()

            # Check that navbar has children (buttons)
            navbar_children = app.navbar.winfo_children()
            assert len(navbar_children) == 5  # 5 navigation buttons


# =============================================================================
# set_managers tests
# =============================================================================


def test_set_managers(root, mock_login_manager, mock_sensor_manager):
    """Test set_managers sets all managers."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        new_sensor_manager = Mock()
        new_camera_manager = Mock()
        new_login_manager = Mock()
        new_config_manager = Mock()

        app.set_managers(
            new_sensor_manager,
            new_camera_manager,
            new_login_manager,
            new_config_manager,
        )

        assert app.sensor_manager == new_sensor_manager
        assert app.camera_manager == new_camera_manager
        assert app.login_manager == new_login_manager
        assert app.configuration_manager == new_config_manager


def test_set_managers_updates_login_page(
    root, mock_login_manager, mock_sensor_manager
):
    """Test set_managers updates login page if it exists."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        mock_login_page = Mock()
        mock_login_page.set_login_manager = Mock()
        app.pages[LoginPage.__name__] = mock_login_page

        new_login_manager = Mock()
        app.set_managers(Mock(), Mock(), new_login_manager)

        mock_login_page.set_login_manager.assert_called_once_with(
            new_login_manager
        )


def test_set_managers_no_login_page(
    root, mock_login_manager, mock_sensor_manager
):
    """Test set_managers when login page does not exist."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        # No login page in pages dict
        new_login_manager = Mock()
        app.set_managers(Mock(), Mock(), new_login_manager)

        # Should not raise exception
        assert app.login_manager == new_login_manager


# =============================================================================
# clean_up_managers tests
# =============================================================================


def test_clean_up_managers(root, mock_login_manager, mock_sensor_manager):
    """Test clean_up_managers clears all managers and closes windows."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        with patch.object(app, "close_all_single_camera_views") as mock_close:
            app.clean_up_managers()

            mock_close.assert_called_once()
            assert app.sensor_manager is None
            assert app.camera_manager is None
            assert app.login_manager is None
            assert app.configuration_manager is None


# =============================================================================
# close_all_single_camera_views tests
# =============================================================================


def test_close_all_single_camera_views_empty(root, mock_login_manager):
    """Test close_all_single_camera_views when no views exist."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=Mock(),
            camera_manager=Mock(),
        )

        app.close_all_single_camera_views()

        assert app.single_camera_views == {}


def test_close_all_single_camera_views_with_windows(
    root, mock_login_manager, mock_sensor_manager
):
    """Test close_all_single_camera_views closes all windows."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        mock_window1 = Mock()
        mock_window1.winfo_exists.return_value = True
        mock_window1.destroy = Mock()

        mock_window2 = Mock()
        mock_window2.winfo_exists.return_value = True
        mock_window2.destroy = Mock()

        app.single_camera_views[1] = mock_window1
        app.single_camera_views[2] = mock_window2

        app.close_all_single_camera_views()

        mock_window1.destroy.assert_called_once()
        mock_window2.destroy.assert_called_once()
        assert app.single_camera_views == {}


def test_close_all_single_camera_views_window_not_exists(
    root, mock_login_manager, mock_sensor_manager
):
    """Test close_all_single_camera_views handles windows that don't exist."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        mock_window = Mock()
        mock_window.winfo_exists.return_value = False
        mock_window.destroy = Mock()

        app.single_camera_views[1] = mock_window

        app.close_all_single_camera_views()

        mock_window.destroy.assert_not_called()
        assert app.single_camera_views == {}


def test_close_all_single_camera_views_exception(
    root, mock_login_manager, mock_sensor_manager
):
    """Test close_all_single_camera_views handles exceptions."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        mock_window = Mock()
        mock_window.winfo_exists.return_value = True
        mock_window.destroy.side_effect = Exception("Destroy failed")

        app.single_camera_views[1] = mock_window

        with patch("builtins.print") as mock_print:
            app.close_all_single_camera_views()

            mock_print.assert_called_once()
            assert "Error closing camera view" in mock_print.call_args[0][0]
            assert app.single_camera_views == {}


# =============================================================================
# open_single_camera_view tests
# =============================================================================


def test_open_single_camera_view_new_window(
    root, mock_login_manager, mock_sensor_manager, mock_camera_manager
):
    """Test open_single_camera_view creates new window."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=mock_camera_manager,
        )

        with patch("core.web_app.SingleCameraViewPage") as mock_page_class:
            mock_window = Mock()
            mock_window.protocol = Mock()
            mock_window.tkraise = Mock()
            mock_page_class.return_value = mock_window

            app.open_single_camera_view(1)

            mock_page_class.assert_called_once()
            assert 1 in app.single_camera_views
            assert app.single_camera_views[1] == mock_window
            mock_window.protocol.assert_called_once()
            mock_window.tkraise.assert_called_once()


def test_open_single_camera_view_existing_window(
    root, mock_login_manager, mock_sensor_manager
):
    """Test open_single_camera_view brings existing window to front."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        mock_window = Mock()
        mock_window.winfo_exists.return_value = True
        mock_window.deiconify = Mock()
        mock_window.focus = Mock()
        mock_window.lift = Mock()

        app.single_camera_views[1] = mock_window

        with patch("core.web_app.SingleCameraViewPage") as mock_page_class:
            app.open_single_camera_view(1)

            # Should not create new window
            mock_page_class.assert_not_called()
            mock_window.deiconify.assert_called_once()
            mock_window.focus.assert_called_once()
            mock_window.lift.assert_called_once()


def test_open_single_camera_view_window_destroyed(
    root, mock_login_manager, mock_sensor_manager
):
    """Test open_single_camera_view removes destroyed window from dict."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        mock_window = Mock()
        mock_window.winfo_exists.return_value = False

        app.single_camera_views[1] = mock_window

        with patch("core.web_app.SingleCameraViewPage") as mock_page_class:
            mock_new_window = Mock()
            mock_new_window.protocol = Mock()
            mock_new_window.tkraise = Mock()
            mock_page_class.return_value = mock_new_window

            app.open_single_camera_view(1)

            # Should remove old and create new
            assert (
                1 not in app.single_camera_views
                or app.single_camera_views[1] == mock_new_window
            )
            mock_page_class.assert_called_once()


def test_open_single_camera_view_exception_handling(
    root, mock_login_manager, mock_sensor_manager
):
    """Test open_single_camera_view handles exception when checking window."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=Mock(),
        )

        mock_window = Mock()
        mock_window.winfo_exists.side_effect = Exception("Check failed")

        app.single_camera_views[1] = mock_window

        with patch("core.web_app.SingleCameraViewPage") as mock_page_class:
            mock_new_window = Mock()
            mock_new_window.protocol = Mock()
            mock_new_window.tkraise = Mock()
            mock_page_class.return_value = mock_new_window

            app.open_single_camera_view(1)

            # Should remove old and create new
            mock_page_class.assert_called_once()


def test_open_single_camera_view_on_close_callback(
    root, mock_login_manager, mock_sensor_manager, mock_camera_manager
):
    """Test open_single_camera_view sets up close callback."""
    with patch.object(WebApp, "draw_page"):
        app = WebApp(
            root,
            login_manager=mock_login_manager,
            sensor_manager=mock_sensor_manager,
            camera_manager=mock_camera_manager,
        )

        with patch("core.web_app.SingleCameraViewPage") as mock_page_class:
            mock_window = Mock()
            mock_window.protocol = Mock()
            mock_window.tkraise = Mock()
            mock_page_class.return_value = mock_window

            app.open_single_camera_view(1)

            # Verify protocol was set
            mock_window.protocol.assert_called_once()
            protocol_call = mock_window.protocol.call_args

            # Call the close callback
            assert 1 in app.single_camera_views
            protocol_call[0][1]()  # Call the lambda
            assert 1 not in app.single_camera_views
