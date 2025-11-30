from typing import Callable

import customtkinter as ctk

from core.pages.interface_page import InterfacePage
from core.pages.utils import show_toast
from manager.login_manager import LoginManager


class LoginPage(InterfacePage):
    def __init__(
        self,
        master,
        page_id: str,
        login_manager: LoginManager,
        on_login_success: Callable[[], None],
        is_system_powered: Callable[[], bool] = None,
        **kwargs,
    ):
        """
        Initialize login page.
        Args:
            master: parent widget (App)
            page_id: page identifier
            login_manager: login manager instance
            on_login_success: callback function to execute \
                when login is successful
            is_system_powered: callback to check if system is powered on
        """
        super().__init__(master, page_id, **kwargs)
        self.login_manager = login_manager
        self.on_login_success = on_login_success
        self.is_system_powered = is_system_powered

        # Initialize widget references
        self.username_entry: ctk.CTkEntry | None = None
        self.password_entry: ctk.CTkEntry | None = None

        # Draw page
        self.draw_page()

    def draw_page(self):
        # Center frame
        center_frame = ctk.CTkFrame(self, corner_radius=10)
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Title
        ctk.CTkLabel(
            center_frame,
            text="SafeHome Login",
            font=("Arial", 24, "bold"),
        ).pack(pady=(40, 30), padx=40)

        # Username
        ctk.CTkLabel(
            center_frame,
            text="Username",
            font=("Arial", 12),
        ).pack(anchor="w", padx=40)

        self.username_entry = ctk.CTkEntry(
            center_frame, font=("Arial", 12), width=200
        )
        self.username_entry.pack(pady=(5, 15), padx=40)
        self.username_entry.bind(
            "<Return>", lambda event: self.password_entry.focus_set()
        )

        # Password
        ctk.CTkLabel(
            center_frame,
            text="Password",
            font=("Arial", 12),
        ).pack(anchor="w", padx=40)

        self.password_entry = ctk.CTkEntry(
            center_frame, font=("Arial", 12), width=200, show="*"
        )
        self.password_entry.pack(pady=(5, 20), padx=40)
        self.password_entry.bind(
            "<Return>", lambda event: self.attempt_login()
        )

        # Login Button
        login_btn = ctk.CTkButton(
            center_frame,
            text="Login",
            font=("Arial", 12, "bold"),
            command=self.attempt_login,
            cursor="hand2",
            width=200,
            height=40,
        )
        login_btn.pack(pady=(0, 40), padx=40)

    def attempt_login(self):
        """
        Internal validation logic called when login button is clicked
        or enter key is pressed.
        """
        # Defensive code to check if widgets are initialized
        if not self.username_entry or not self.password_entry:
            return

        username = self.username_entry.get()
        password = self.password_entry.get()

        # check if system is powered
        if self.is_system_powered and not self.is_system_powered():
            show_toast(self.master, "System is not powered on")
            return

        # fallback: check login_manager existence (for backward compatibility)
        if self.login_manager is None:
            show_toast(self.master, "System is not powered on")
            return

        # 1. Validate username and password
        if not username or not password:
            show_toast(self.master, "username and password are required")
            return

        # 2. Login
        if self.login_manager.login_web(username, password):
            self.on_login_success()
        else:
            show_toast(self.master, "username or password is incorrect")

    def set_login_manager(self, login_manager: LoginManager):
        self.login_manager = login_manager
