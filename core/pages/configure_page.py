import customtkinter as ctk

from core.pages.interface_page import InterfacePage


class ConfigurePage(InterfacePage):
    def __init__(
        self,
        master,
        page_id,
        configuration_manager,
        login_manager=None,
        current_user_id=None,
        show_log_page=None,
        **kwargs,
    ):
        super().__init__(master, page_id, **kwargs)
        self.configuration_manager = configuration_manager
        self.login_manager = login_manager
        self.current_user_id = current_user_id
        self.show_log_page = show_log_page
        self.draw_page()

    def draw_page(self):
        # Main container for center alignment (changed to scrollable)
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            container, text="Configuration", font=("Arial", 24, "bold")
        ).pack(pady=(0, 20), anchor="w")

        # 1. System Settings
        self._create_section(container, "System Settings")
        self._create_setting_switch(container, "System Notifications")
        self._create_setting_switch(container, "Auto-Update Firmware")

        # 2. User Settings
        self._create_section(container, "User Settings")
        self._create_setting_row(
            container, "Current User", self.current_user_id
        )
        self._create_editable_setting(
            container,
            "Panic Phone Number",
            "panic_phone_number",
            "get_panic_phone_number",
            input_type="text",
            placeholder="e.g., 119",
        )
        self._create_editable_setting(
            container,
            "Homeowner Phone Number",
            "homeowner_phone_number",
            "get_homeowner_phone_number",
            input_type="text",
            placeholder="e.g., 010-1234-5678",
        )
        self._create_editable_setting(
            container,
            "System Lock Time",
            "system_lock_time",
            "get_system_lock_time",
            input_type="int",
            placeholder="e.g., 30 (minutes)",
        )
        self._create_editable_setting(
            container,
            "Alarm Delay Time",
            "alarm_delay_time",
            "get_alarm_delay_time",
            input_type="int",
            placeholder="e.g., 60 (minutes)",
        )
        self._create_setting_button(
            container,
            "Change Password",
            command=self._show_change_password_dialog,
        )

        # 3. About
        self._create_section(container, "About")
        self._create_setting_row(container, "Version", "v1.0.0-alpha")
        self._create_setting_button(
            container,
            "View System Logs",
            color="#34495e",
            command=self.show_log_page,
        )

    def _create_section(self, parent, title):
        ctk.CTkLabel(
            parent, text=title, font=("Arial", 16, "bold"), text_color="gray"
        ).pack(pady=(20, 10), anchor="w")

    def _create_setting_switch(self, parent, text):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        ctk.CTkLabel(frame, text=text, font=("Arial", 14)).pack(side="left")
        ctk.CTkSwitch(frame, text="").pack(side="right")

    def _create_setting_row(self, parent, label, value):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        ctk.CTkLabel(frame, text=label, font=("Arial", 14)).pack(side="left")
        ctk.CTkLabel(frame, text=value, font=("Arial", 14, "bold")).pack(
            side="right"
        )

    def _create_setting_button(self, parent, text, color=None, command=None):
        ctk.CTkButton(
            parent,
            text=text,
            height=35,
            fg_color=color,
            font=("Arial", 13),
            command=command,
        ).pack(fill="x", pady=5)

    def _create_dialog_button(
        self, parent, text, width=120, height=35, color=None, command=None
    ):
        """Create a button for dialog windows."""
        return ctk.CTkButton(
            parent,
            text=text,
            width=width,
            height=height,
            fg_color=color,
            font=("Arial", 13),
            command=command,
        )

    def _create_editable_setting(
        self,
        parent,
        label,
        field_name,
        getter_method,
        input_type="text",
        placeholder="",
    ):
        """Create an editable setting row with current value and change button.

        Args:
            parent: Parent widget
            label: Display label
            field_name: Field name in configuration (e.g. 'panic_phone_number')
            getter_method: Method name to get current value
            (e.g. 'get_panic_phone_number')
            input_type: Type of input ('text' or 'int')
            placeholder: Placeholder text for input dialog
        """
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=5)

        ctk.CTkLabel(frame, text=label, font=("Arial", 14)).pack(side="left")

        # Get current value from configuration manager
        current_value = "Not Set"
        if self.configuration_manager:
            try:
                system_settings = (
                    self.configuration_manager.get_system_setting()
                )
                if system_settings:
                    value = getattr(system_settings, getter_method)()
                    if value and str(value) != "None":
                        if input_type == "int":
                            current_value = f"{value} min"
                        else:
                            current_value = str(value)
            except Exception as e:
                print(f"Error fetching {field_name}: {e}")

        # Current value display
        value_label = ctk.CTkLabel(
            frame, text=current_value, font=("Arial", 14, "bold")
        )
        value_label.pack(side="left", padx=(10, 0))

        # Change button
        ctk.CTkButton(
            frame,
            text="Change",
            width=80,
            height=28,
            font=("Arial", 12),
            command=lambda: self._show_input_dialog(
                label,
                field_name,
                getter_method,
                value_label,
                input_type,
                placeholder,
            ),
        ).pack(side="right")

    def _show_input_dialog(
        self,
        label,
        field_name,
        getter_method,
        value_label,
        input_type,
        placeholder,
    ):
        """Show dialog to input new value for any setting field.

        Args:
            label: Display label for the dialog
            field_name: Field name in configuration
            getter_method: Method name to get current value
            value_label: Label widget to update after change
            input_type: Type of input ('text' or 'int')
            placeholder: Placeholder text for input field
        """
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Change {label}")
        dialog.geometry("400x250")
        dialog.transient(self)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (400 // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (200 // 2)
        dialog.geometry(f"+{x}+{y}")

        # Title
        ctk.CTkLabel(
            dialog,
            text=f"Enter New {label}",
            font=("Arial", 16, "bold"),
        ).pack(pady=(20, 10))

        # Input field
        entry = ctk.CTkEntry(
            dialog,
            placeholder_text=placeholder,
            width=300,
            height=40,
            font=("Arial", 14),
        )
        entry.pack(pady=10)

        # Load current value from configuration manager
        if self.configuration_manager:
            try:
                system_settings = (
                    self.configuration_manager.get_system_setting()
                )
                if system_settings:
                    current_value = getattr(system_settings, getter_method)()
                    if current_value and str(current_value) != "None":
                        entry.insert(0, str(current_value))
            except Exception as e:
                print(f"Error loading current value: {e}")

        entry.focus()

        # Button frame
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=20)

        def confirm_change():
            new_value = entry.get().strip()
            if not new_value:
                return

            # Convert to appropriate type
            try:
                if input_type == "int":
                    new_value = int(new_value)
            except ValueError:
                print(f"Invalid input: expected {input_type}")
                return

            # Update in configuration manager
            if not self.configuration_manager:
                print("Configuration manager not available")
                return

            # Get current system settings and update the specific field
            current_settings = self.configuration_manager.get_system_setting()
            if not current_settings:
                print("No system settings found")
                return

            # Call the setter method instead of direct attribute assignment
            # to ensure validation logic is executed
            setter_method_name = getter_method.replace("get_", "set_")
            setter_method = getattr(current_settings, setter_method_name, None)

            if setter_method and callable(setter_method):
                try:
                    result = setter_method(new_value)
                    if not result:
                        print(
                            f"Failed to set {field_name}: setter returns False"
                        )
                        return
                except ValueError as e:
                    print(f"Validation error for {field_name}: {e}")
                    return
            else:
                # Fallback to direct assignment if setter doesn't exist
                setattr(current_settings, field_name, new_value)

            # Update system settings in DB
            if not self.configuration_manager.update_system_setting(
                current_settings.to_schema()
            ):
                print(f"Failed to update {field_name}")
                return

            # update display
            if input_type == "int":
                value_label.configure(text=f"{new_value} min")
            else:
                value_label.configure(text=str(new_value))

            dialog.destroy()

        # Confirm button
        self._create_dialog_button(
            button_frame, "Confirm", command=confirm_change
        ).pack(side="left", padx=5)

        # Cancel button
        self._create_dialog_button(
            button_frame, "Cancel", color="gray", command=dialog.destroy
        ).pack(side="left", padx=5)

        # Enter key binding
        entry.bind("<Return>", lambda e: confirm_change())

    def _show_change_password_dialog(self):
        """Show password change dialog without verification."""
        if not self.login_manager:
            print("LoginManager not available")
            return

        # Directly show password management dialog
        self._show_password_management_dialog()

    def _show_password_management_dialog(self):
        """Show password management dialog for user web, panel, and guest."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Password Management")
        dialog.geometry("500x500")
        dialog.transient(self)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - 250
        y = self.winfo_rooty() + (self.winfo_height() // 2) - 200
        dialog.geometry(f"+{x}+{y}")

        # Title
        title_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(
            title_frame, text="Change Passwords", font=("Arial", 18, "bold")
        ).pack()

        # Container for password rows
        container = ctk.CTkFrame(dialog, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=10)

        # 1. User Web Password
        self._create_password_row(
            container, "User Web Password", "web", self.current_user_id
        )

        # 2. User Panel Password
        self._create_password_row(
            container, "User Panel Password", "panel", self.current_user_id
        )

        # 3. Guest Password with disable option
        self._create_guest_password_row(container)

        # Close button
        self._create_dialog_button(
            dialog, "Close", width=150, height=40, command=dialog.destroy
        ).pack(pady=20)

    def _create_password_row(self, parent, label, pw_type, user_id):
        """Create a password change row."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=10)

        ctk.CTkLabel(frame, text=label, font=("Arial", 14)).pack(side="left")

        ctk.CTkLabel(frame, text=" ", font=("Arial", 14)).pack(
            side="left", padx=(10, 0)
        )

        ctk.CTkButton(
            frame,
            text="Change",
            width=80,
            height=28,
            font=("Arial", 12),
            command=lambda: self._show_new_password_input(
                label, pw_type, user_id
            ),
        ).pack(side="right")

    def _create_guest_password_row(self, parent):
        """Create guest password row."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=10)

        ctk.CTkLabel(frame, text="Guest Password", font=("Arial", 14)).pack(
            side="left"
        )

        ctk.CTkLabel(frame, text=" ", font=("Arial", 14)).pack(
            side="left", padx=(10, 0)
        )

        ctk.CTkButton(
            frame,
            text="Change",
            width=80,
            height=28,
            font=("Arial", 12),
            command=lambda: self._show_guest_password_input(),
        ).pack(side="right")

    def _show_guest_password_input(self):
        """Handle guest password change with NULL check."""
        # Check if guest password is NULL
        try:
            result = self.login_manager.storage_manager.execute_query(
                "SELECT panel_password FROM users WHERE panel_id = 'guest'",
                (),
            )
            current_password = result[0][0] if result and result[0] else None

            if current_password is None:
                # Guest password is disabled, go directly to new password
                self._show_new_guest_password_dialog(None)
            else:
                # Guest password exists, verify it first
                self._show_new_password_input(
                    "Guest Password", "panel", "guest"
                )
        except Exception as e:
            print(f"Error checking guest password: {e}")

    def _show_new_password_input(self, label, pw_type, user_id):
        """Show dialog to verify current password first."""
        # Step 1: Verify current password
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Change {label}")
        dialog.geometry("400x250")
        dialog.transient(self)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - 200
        y = self.winfo_rooty() + (self.winfo_height() // 2) - 90
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            dialog,
            text=f"Enter Current {label}",
            font=("Arial", 14, "bold"),
        ).pack(pady=(20, 10))

        old_pw_entry = ctk.CTkEntry(
            dialog,
            placeholder_text="Current password",
            show="*",
            width=300,
            height=40,
        )
        old_pw_entry.pack(pady=10)
        old_pw_entry.focus()

        # Error message label (hidden initially)
        error_label = ctk.CTkLabel(
            dialog, text="", font=("Arial", 11), text_color="red", height=0
        )
        error_label.pack()

        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=15)

        def verify_and_continue():
            old_password = old_pw_entry.get()
            if not old_password:
                error_label.configure(
                    text="Please enter current password", height=20
                )
                return

            # Clear previous error
            error_label.configure(text="", height=0)

            # Verify current password
            is_valid = False
            try:
                if pw_type == "web":
                    is_valid = self.login_manager._verify_web_password(
                        user_id, old_password
                    )
                elif pw_type == "panel":
                    is_valid = self.login_manager._verify_panel_password(
                        user_id, old_password
                    )

                if is_valid:
                    # Step 2: Show new password input
                    dialog.destroy()
                    if user_id == "guest":
                        self._show_new_guest_password_dialog(old_password)
                    else:
                        self._show_new_password_dialog(
                            label, pw_type, user_id, old_password
                        )
                else:
                    old_pw_entry.delete(0, "end")
                    old_pw_entry.focus()
                    error_label.configure(
                        text="Incorrect password! Try again", height=20
                    )
            except Exception as e:
                print(f"Error verifying password: {e}")
                error_label.configure(text=f"Error: {str(e)}", height=20)

        self._create_dialog_button(
            button_frame, "Confirm", command=verify_and_continue
        ).pack(side="left", padx=5)

        self._create_dialog_button(
            button_frame, "Cancel", color="gray", command=dialog.destroy
        ).pack(side="left", padx=5)

        old_pw_entry.bind("<Return>", lambda e: verify_and_continue())

    def _show_new_password_dialog(self, label, pw_type, user_id, old_password):
        """Show dialog to input new password after verification."""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Change {label}")
        dialog.geometry("400x250")
        dialog.transient(self)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - 200
        y = self.winfo_rooty() + (self.winfo_height() // 2) - 100
        dialog.geometry(f"+{x}+{y}")

        # Title with requirements
        if pw_type == "panel":
            req_text = "4-digit number"
        else:
            req_text = "8 characters"

        title_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        title_frame.pack(pady=(20, 10))

        ctk.CTkLabel(
            title_frame, text=f"Enter New {label}", font=("Arial", 16, "bold")
        ).pack()

        ctk.CTkLabel(
            title_frame,
            text=f"({req_text})",
            font=("Arial", 11),
            text_color="gray",
        ).pack()

        password_entry = ctk.CTkEntry(
            dialog,
            placeholder_text="New password",
            show="*",
            width=300,
            height=40,
            font=("Arial", 14),
        )
        password_entry.pack(pady=10)
        password_entry.focus()

        # Error message label
        error_label = ctk.CTkLabel(
            dialog, text="", font=("Arial", 11), text_color="red"
        )
        error_label.pack()

        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=15)

        def confirm_change():
            new_password = password_entry.get()
            if not new_password:
                error_label.configure(text="Please enter a password")
                return

            # Clear previous error
            error_label.configure(text="")

            success = False
            try:
                if pw_type == "web":
                    success = self.login_manager.change_web_password(
                        user_id, old_password, new_password
                    )
                elif pw_type == "panel":
                    success = self.login_manager.change_panel_password(
                        user_id, old_password, new_password
                    )

                if success:
                    dialog.destroy()
                    print(f"{label} changed successfully")
                else:
                    password_entry.delete(0, "end")
                    password_entry.focus()
                    error_label.configure(
                        text=f"Invalid password! Must be {req_text}"
                    )
            except Exception as e:
                print(f"Error changing password: {e}")
                error_label.configure(text=f"Error: {str(e)}")

        self._create_dialog_button(
            button_frame, "Confirm", command=confirm_change
        ).pack(side="left", padx=5)

        self._create_dialog_button(
            button_frame, "Cancel", color="gray", command=dialog.destroy
        ).pack(side="left", padx=5)

        password_entry.bind("<Return>", lambda e: confirm_change())

    def _show_new_guest_password_dialog(self, old_password):
        """Show dialog for guest password with disable option."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Change Guest Password")
        dialog.geometry("400x250")
        dialog.transient(self)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - 200
        y = self.winfo_rooty() + (self.winfo_height() // 2) - 125
        dialog.geometry(f"+{x}+{y}")

        # Title
        title_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        title_frame.pack(pady=(20, 10))

        ctk.CTkLabel(
            title_frame,
            text="Set Guest Password",
            font=("Arial", 16, "bold"),
        ).pack()

        ctk.CTkLabel(
            title_frame,
            text="(4-digit number)",
            font=("Arial", 11),
            text_color="gray",
        ).pack()

        # Password entry
        password_entry = ctk.CTkEntry(
            dialog,
            placeholder_text="New password",
            show="*",
            width=300,
            height=40,
            font=("Arial", 14),
        )
        password_entry.pack(pady=10)
        password_entry.focus()

        # Disable checkbox
        disable_var = ctk.BooleanVar(value=False)
        disable_check = ctk.CTkCheckBox(
            dialog,
            text="Disable guest password (set to NULL)",
            variable=disable_var,
            font=("Arial", 12),
        )
        disable_check.pack(pady=5)

        # Error message label
        error_label = ctk.CTkLabel(
            dialog, text="", font=("Arial", 11), text_color="red", height=0
        )
        error_label.pack()

        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=15)

        def toggle_password_entry():
            if disable_var.get():
                password_entry.configure(state="disabled")
            else:
                password_entry.configure(state="normal")

        disable_check.configure(command=toggle_password_entry)

        def confirm_change():
            if disable_var.get():
                # Disable guest password
                try:
                    result = self.login_manager.storage_manager.execute_query(
                        """UPDATE users SET panel_password = NULL,
                        updated_at = CURRENT_TIMESTAMP
                        WHERE panel_id = 'guest'""",
                        (),
                    )
                    if result is not None:
                        dialog.destroy()
                        print("Guest password disabled successfully")
                    else:
                        error_label.configure(
                            text="Failed to disable password", height=20
                        )
                except Exception as e:
                    print(f"Error disabling guest password: {e}")
                    error_label.configure(text=f"Error: {str(e)}", height=20)
            else:
                # Set new password
                new_password = password_entry.get()
                if not new_password:
                    error_label.configure(
                        text="Please enter a password", height=20
                    )
                    return

                error_label.configure(text="", height=0)

                success = False
                try:
                    if old_password is None:
                        # Guest password was NULL, directly set new password
                        if not self.login_manager._validate_panel_password(
                            new_password
                        ):
                            error_label.configure(
                                text="Invalid! Must be 4-digit number",
                                height=20,
                            )
                            return

                        result = (
                            self.login_manager.storage_manager.execute_query(
                                """UPDATE users SET panel_password = ?,
                                updated_at = CURRENT_TIMESTAMP
                                WHERE panel_id = 'guest'""",
                                (new_password,),
                            )
                        )
                        success = result is not None
                    else:
                        # Guest password exists, use change method
                        success = self.login_manager.change_panel_password(
                            "guest", old_password, new_password
                        )

                    if success:
                        dialog.destroy()
                        print("Guest password changed successfully")
                    else:
                        password_entry.delete(0, "end")
                        password_entry.focus()
                        error_label.configure(
                            text="Invalid! Must be 4-digit number", height=20
                        )
                except Exception as e:
                    print(f"Error changing password: {e}")
                    error_label.configure(text=f"Error: {str(e)}", height=20)

        self._create_dialog_button(
            button_frame, "Confirm", command=confirm_change
        ).pack(side="left", padx=5)

        self._create_dialog_button(
            button_frame, "Cancel", color="gray", command=dialog.destroy
        ).pack(side="left", padx=5)

        password_entry.bind("<Return>", lambda e: confirm_change())
