from typing import Any, Optional

import customtkinter as ctk

from core.pages.configure_page import ConfigurePage
from core.pages.interface_page import InterfacePage, InterfaceWindow
from core.pages.login_page import LoginPage
from core.pages.multi_camera_view_page import MultiCameraViewPage
from core.pages.safehome_mode_page import SafeHomeModePage
from core.pages.security_page import SecurityPage
from core.pages.sensors_management_page import SensorsManagementPage
from core.pages.single_camera_view_page import SingleCameraViewPage
from core.pages.surveillance_page import SurveillancePage
from core.pages.utils import show_toast
from core.pages.view_log_page import ViewLogPage
from manager.camera_manager import CameraManager
from manager.configuration_manager import ConfigurationManager
from manager.login_manager import LoginManager
from manager.sensor_manager import SensorManager

NAVBAR_HEIGHT = 60
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 500

# Theme settings (System, Dark, Light)
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class WebApp(InterfaceWindow):
    def __init__(
        self,
        master,
        login_manager: Optional[LoginManager],
        sensor_manager: Optional[SensorManager],
        camera_manager: Optional[CameraManager],
        configuration_manager: Optional[ConfigurationManager] = None,
        page_id: str = "WebApp",
        title: str = "SafeHome Web App",
        **kwargs,
    ):
        super().__init__(
            master,
            page_id,
            title,
            window_width=WINDOW_WIDTH,
            window_height=WINDOW_HEIGHT,
            **kwargs,
        )
        self.resizable(False, False)

        # init managers
        self.login_manager = login_manager
        self.sensor_manager = sensor_manager
        self.camera_manager = camera_manager
        self.configuration_manager = configuration_manager

        self.navbar = None
        self.content = None
        self.pages: dict[str, InterfacePage | InterfaceWindow] = {}
        # 동적으로 생성된 SingleCameraView 페이지들을 추적
        self.single_camera_views: dict[int, InterfaceWindow] = {}
        self.container = ctk.CTkFrame(
            self,
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            corner_radius=0,
        )
        self.container.place(x=0, y=0)

        # Draw page
        self.draw_page()

    def draw_page(self):
        """Draw the page UI elements based on login status."""
        if not self.login_manager or not self.login_manager.is_logged_in_web:
            # 로그인 전: 로그인 페이지만 표시
            self.draw_login_page()
        else:
            # 로그인 후: 메인 인터페이스 표시
            self.draw_main_interface()

    def is_system_powered(self) -> bool:
        """
        Check if the system (ControlPanel) is powered on.
        Returns:
            bool: True if system is powered, False otherwise
        """
        # Check if master (ControlPanel) has powered attribute
        if hasattr(self.master, "powered"):
            return self.master.powered
        return False

    def draw_login_page(self):
        """Draw login page only."""
        # 동적으로 생성된 SingleCameraView 창들 모두 닫기
        self.close_all_single_camera_views()

        # destroy all pages (except login page)
        pages_to_destroy = [
            name for name in self.pages.keys() if name != LoginPage.__name__
        ]
        for name in pages_to_destroy:
            self.destroy_page(name)

        # 로그인 페이지 생성 및 표시
        name = LoginPage.__name__
        if self.pages.get(name) is None:
            self.register_page(
                LoginPage,
                master=self,
                login_manager=self.login_manager,
                on_login_success=self.switch_to_main,
                is_system_powered=self.is_system_powered,
            )

        # show login page
        self.show_page(name)

    def draw_main_interface(self):
        """Draw main interface with navbar and content area."""
        # hide all pages
        for name in list(self.pages.keys()):
            self.hide_page(name)

        # initialize main interface
        self.init_main_interface()

        # show default page (SecurityPage)
        self.show_page("SecurityPage")

    def switch_to_main(self):
        """
        Callback invoked on successful login.
        Cleans up login page and initializes main interface.
        """
        # Check if system is powered
        if not self.is_system_powered():
            show_toast(self, "Control Panel is not powered")
            return

        # Draw main interface
        self.draw_page()

        # Show default page (SecurityPage)
        self.show_page("SecurityPage")

    def register_page(
        self,
        page_class: type[InterfacePage | InterfaceWindow | Any],
        master=None,
        *args,
        **kwargs,
    ):
        """
        Create instance from page class and register to management dictionary.
        Handles InterfacePage(Frame) and InterfaceWindow(Toplevel) separately.
        """
        name = page_class.__name__

        # 1. InterfaceWindow (new window)
        if issubclass(page_class, InterfaceWindow):
            # Set master to self(App) for Toplevel
            master = self if master is None else master
            page = page_class(master, page_id=name, *args, **kwargs)
            page.withdraw()  # Initially hidden
            # Hide instead of destroy when close button(X) clicked (for reuse)
            page.protocol("WM_DELETE_WINDOW", page.withdraw)
            self.pages[name] = page

        # 2. InterfacePage (internal frame)
        elif issubclass(page_class, InterfacePage):
            # Set content frame as master for Frame
            master = self.content if master is None else master
            page = page_class(master, page_id=name, *args, **kwargs)
            self.pages[name] = page

        # 3. if others
        else:
            # Handle direct CustomTkinter Frame inheritance like InterfacePage
            if issubclass(page_class, ctk.CTkFrame):
                # Set content frame as master for Frame
                master = self.content if master is None else master
                page = page_class(master)
                self.pages[name] = page
            else:
                print(f"Error: Unknown page type for {name}")

    def show_page(self, name: str):
        """
        Display the page with the given name.
        - Frame: Raise to top (tkraise)
        - Window: Show and focus (deiconify)
        """
        if name not in self.pages:
            print(f"Page '{name}' not found.")
            return

        page = self.pages[name]

        if isinstance(page, InterfaceWindow):
            # page.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)
            page.deiconify()  # Show window
            page.focus()  # Set focus
        elif isinstance(page, InterfacePage):  # Including InterfacePage
            page.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)
            page.tkraise()  # Raise frame to top
        else:
            page.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)
            page.tkraise()

    def hide_page(self, name: str):
        """
        Hide the page with the given name.
        - InterfaceWindow: withdraw()
        - InterfacePage: place_forget()
        """
        if name not in self.pages:
            print(f"Page '{name}' not found.")
            return

        page = self.pages[name]
        if isinstance(page, InterfaceWindow):
            page.withdraw()
        elif isinstance(page, InterfacePage):
            page.place_forget()
        else:
            # For other CTkFrame-based widgets
            page.place_forget()

    def destroy_page(self, name: str):
        """
        Destroy the page with the given name and remove from pages dict.
        """
        if name not in self.pages:
            print(f"Page '{name}' not found.")
            return

        page = self.pages[name]
        try:
            page.destroy()
        except Exception as e:
            print(f"Failed to destroy page '{name}': {e}")
        finally:
            del self.pages[name]

    def init_main_interface(self):
        """Initialize main interface with navbar and content area."""
        # ===== 1. Top Navigation Area =====
        self.navbar = ctk.CTkFrame(
            self,
            width=WINDOW_WIDTH,
            height=NAVBAR_HEIGHT,
            corner_radius=0,
            fg_color="#2c3e50",
        )
        self.navbar.place(x=0, y=0)

        # ===== 2. Main Content Area =====
        self.content = ctk.CTkFrame(
            self,
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT - NAVBAR_HEIGHT,
            corner_radius=0,
        )
        self.content.place(x=0, y=NAVBAR_HEIGHT)

        # ===== 3. Page Registration and Creation =====
        # define page configuration (PageClass, kwargs)
        pages_config = [
            (
                SecurityPage,
                {
                    "sensor_manager": self.sensor_manager,
                    "login_manager": self.login_manager,
                    "configuration_manager": self.configuration_manager,
                },
            ),
            (
                SafeHomeModePage,
                {
                    "sensor_manager": self.sensor_manager,
                    "configuration_manager": self.configuration_manager,
                },
            ),
            (
                SurveillancePage,
                {
                    "camera_manager": self.camera_manager,
                    "show_multi_camera": lambda: self.show_page(
                        "MultiCameraViewPage"
                    ),
                    "show_single_camera": self.open_single_camera_view,
                },
            ),
            (
                MultiCameraViewPage,
                {
                    "camera_manager": self.camera_manager,
                    "initially_hidden": False,
                    "show_single_camera": self.open_single_camera_view,
                },
            ),
            (ViewLogPage, {}),
            (
                ConfigurePage,
                {
                    "show_log_page": lambda: self.show_page("ViewLogPage"),
                    "configuration_manager": self.configuration_manager,
                    "login_manager": self.login_manager,
                    "current_user_id": (
                        self.login_manager.current_user_id
                        if self.login_manager
                        else None
                    ),
                },
            ),
            (SensorsManagementPage, {"sensor_manager": self.sensor_manager}),
        ]
        for page_class, kwargs in pages_config:
            self.register_page(page_class, **kwargs)

        # ===== 4. Top Navigation Buttons =====
        def create_nav_btn(text, command):
            return ctk.CTkButton(
                self.navbar,
                text=text,
                command=command,
                font=("Arial", 12, "bold"),
                fg_color="transparent",
                hover_color="#1abc9c",
                text_color="#fdfefe",
                width=100,
                height=40,
                corner_radius=5,
            )

        btn_security = create_nav_btn(
            "Security", lambda: self.show_page("SecurityPage")
        )
        btn_mode = create_nav_btn(
            "Mode", lambda: self.show_page("SafeHomeModePage")
        )
        btn_surveillance = create_nav_btn(
            "Surveillance", lambda: self.show_page("SurveillancePage")
        )
        btn_config = create_nav_btn(
            "Configure", lambda: self.show_page("ConfigurePage")
        )
        btn_sensors = create_nav_btn(
            "Sensors", lambda: self.show_page("SensorsManagementPage")
        )

        btn_security.pack(side="left", padx=(20, 10), pady=10)
        btn_mode.pack(side="left", padx=10, pady=10)
        btn_surveillance.pack(side="left", padx=10, pady=10)
        btn_config.pack(side="left", padx=10, pady=10)
        btn_sensors.pack(side="left", padx=10, pady=10)

    def set_managers(
        self,
        sensor_manager: SensorManager,
        camera_manager: CameraManager,
        login_manager: LoginManager,
        configuration_manager: ConfigurationManager = None,
    ):
        """Set managers to the web app."""
        self.sensor_manager = sensor_manager
        self.camera_manager = camera_manager
        self.login_manager = login_manager
        self.configuration_manager = configuration_manager

        # set login manager to login page (if exists)
        if LoginPage.__name__ in self.pages:
            self.pages[LoginPage.__name__].set_login_manager(login_manager)

    def clean_up_managers(self):
        """Clean up managers and close all dynamic windows."""
        # 동적으로 생성된 창들 모두 닫기
        self.close_all_single_camera_views()

        self.sensor_manager = None
        self.camera_manager = None
        self.login_manager = None
        self.configuration_manager = None

    def close_all_single_camera_views(self):
        """
        Close all dynamically created SingleCameraView windows.
        시스템이 종료되거나 로그아웃 시 모든 카메라 뷰 창을 닫습니다.
        """
        # 모든 SingleCameraView 창 닫기
        camera_ids_to_close = list(self.single_camera_views.keys())
        for camera_id in camera_ids_to_close:
            window = self.single_camera_views[camera_id]
            try:
                if window.winfo_exists():
                    window.destroy()
            except Exception as e:
                print(f"Error closing camera view {camera_id}: {e}")

        # 딕셔너리 초기화
        self.single_camera_views.clear()

    def open_single_camera_view(self, camera_id: int):
        """
        Open a single camera view window for the specified camera.
        SingleCameraViewPage는 동적으로 camera_id를 받아야 하므로
        register_page로 등록하지 않고 필요할 때마다 생성합니다.

        같은 camera_id의 창이 이미 열려있으면 새로 생성하지 않고
        기존 창을 앞으로 가져옵니다.

        Args:
            camera_id: ID of the camera to view
        """
        # 이미 해당 카메라의 창이 열려있는지 확인
        if camera_id in self.single_camera_views:
            existing_window = self.single_camera_views[camera_id]
            # 창이 아직 존재하는지 확인 (winfo_exists로 확인)
            try:
                if existing_window.winfo_exists():
                    # 창을 앞으로 가져오기
                    existing_window.deiconify()  # 최소화 해제
                    existing_window.focus()  # 포커스
                    existing_window.lift()  # 최상단으로
                    return
                else:
                    # 창이 이미 파괴되었으면 딕셔너리에서 제거
                    del self.single_camera_views[camera_id]
            except Exception:
                # 창이 더 이상 유효하지 않으면 딕셔너리에서 제거
                del self.single_camera_views[camera_id]

        # 새 창 생성
        window = SingleCameraViewPage(
            master=self,
            page_id=f"single_camera_view_{camera_id}",
            camera_manager=self.camera_manager,
            camera_id=camera_id,
            initially_hidden=False,
        )

        # 딕셔너리에 추가
        self.single_camera_views[camera_id] = window

        # 창이 닫힐 때 딕셔너리에서 제거
        def on_window_close():
            if camera_id in self.single_camera_views:
                del self.single_camera_views[camera_id]

        window.protocol(
            "WM_DELETE_WINDOW", lambda: (on_window_close(), window.destroy())
        )

        window.tkraise()
