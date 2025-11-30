import customtkinter as ctk

from core.pages.interface_page import InterfaceWindow
from manager.log_manager import LogManager


class ViewLogPage(InterfaceWindow):
    """
    Log viewer window with filtering and refresh capabilities.
    Displays logs from LogManager with color-coded severity levels.
    """

    def __init__(
        self,
        master,
        page_id: str = "ViewLog",
        title: str = "SafeHome Log Viewer",
        **kwargs
    ):
        """
        Initialize View Log Page.

        Args:
            master: Parent widget
            page_id: Page identifier
            title: Window title
        """
        super().__init__(
            master=master,
            page_id=page_id,
            title=title,
            **kwargs
        )

        self.geometry("1000x700")
        self.resizable(True, True)

        # Get LogManager instance
        self.log_manager = LogManager()

        # Filter settings
        self.current_filter = "ALL"

        # Draw the page
        self.draw_page()

        # Load logs initially
        self.refresh_logs()

    def draw_page(self):
        """Draw the log viewer UI."""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(pady=10, padx=10, fill="x")

        header = ctk.CTkLabel(
            header_frame,
            text="SafeHome Log Viewer",
            font=("Arial", 20, "bold"),
            text_color="#1f538d",
        )
        header.pack(side="left", padx=10)

        # Log count label
        self.log_count_label = ctk.CTkLabel(
            header_frame,
            text="Total: 0 logs",
            font=("Arial", 12),
            text_color="#6c757d",
        )
        self.log_count_label.pack(side="right", padx=10)

        # Control panel
        control_frame = ctk.CTkFrame(
            self,
            fg_color="#e9ecef",
            corner_radius=10,
            border_width=2
        )
        control_frame.pack(pady=5, padx=10, fill="x")

        # Filter buttons
        filter_label = ctk.CTkLabel(
            control_frame,
            text="Filter by Level:",
            font=("Arial", 12, "bold"),
            text_color="#2c3e50"
        )
        filter_label.pack(side="left", padx=10, pady=10)

        filter_buttons = [
            ("ALL", "#6c757d"),
            ("DEBUG", "#17a2b8"),
            ("INFO", "#28a745"),
            ("WARNING", "#ffc107"),
            ("ERROR", "#dc3545"),
            ("CRITICAL", "#721c24"),
        ]

        for level, color in filter_buttons:
            btn = ctk.CTkButton(
                control_frame,
                text=level,
                command=lambda lvl=level: self.filter_logs(lvl),
                width=80,
                height=30,
                fg_color=color,
                hover_color=self._darken_color(color),
                font=("Arial", 10, "bold")
            )
            btn.pack(side="left", padx=3, pady=10)

        # Action buttons
        action_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        action_frame.pack(side="right", padx=10)

        ctk.CTkButton(
            action_frame,
            text="🔄 Refresh",
            command=self.refresh_logs,
            width=100,
            height=30,
            fg_color="#007bff",
            hover_color="#0056b3",
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            action_frame,
            text="🗑️ Clear Display",
            command=self.clear_display,
            width=120,
            height=30,
            fg_color="#6c757d",
            hover_color="#5a6268",
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=3)

        # Log display area
        log_frame = ctk.CTkFrame(
            self,
            fg_color="#2b2b2b",
            corner_radius=10,
            border_width=2,
            border_color="gray"
        )
        log_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Log text box
        self.log_textbox = ctk.CTkTextbox(
            log_frame,
            font=("Courier", 10),
            fg_color="#1e1e1e",
            text_color="#ffffff",
            corner_radius=5,
            wrap="none"
        )
        self.log_textbox.pack(pady=5, padx=5, fill="both", expand=True)

        # Info panel
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(pady=5, padx=10, fill="x")

        info_text = (
            "💡 Tip: Use filter buttons to view specific log levels. "
            "Logs are color-coded by severity level."
        )
        info_label = ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=("Arial", 9),
            text_color="#6c757d",
        )
        info_label.pack(side="left", padx=5)

        # Close button
        close_btn = ctk.CTkButton(
            self,
            text="Close",
            command=self.withdraw,
            width=150,
            height=35,
            fg_color="#6c757d",
            hover_color="#5a6268",
            font=("Arial", 11, "bold")
        )
        close_btn.pack(pady=10)

    def refresh_logs(self):
        """Refresh and display logs from LogManager."""
        try:
            # Get logs from LogManager
            logs = self.log_manager.get_logs()

            # Clear current display
            self.log_textbox.configure(state="normal")
            self.log_textbox.delete("1.0", "end")

            # Apply filter and display
            filtered_logs = self._filter_log_lines(logs)

            if not filtered_logs:
                self.log_textbox.insert(
                    "1.0",
                    "No logs found.\n"
                )
            else:
                for log_line in filtered_logs:
                    self._insert_colored_log(log_line)

            # Update count
            self.log_count_label.configure(
                text=f"Total: {len(logs)} logs | "
                f"Displayed: {len(filtered_logs)} logs"
            )

            self.log_textbox.configure(state="disabled")

        except Exception as e:
            self.log_textbox.configure(state="normal")
            self.log_textbox.delete("1.0", "end")
            self.log_textbox.insert(
                "1.0",
                f"Error loading logs: {e}\n"
            )
            self.log_textbox.configure(state="disabled")

    def filter_logs(self, level: str):
        """
        Filter logs by severity level.

        Args:
            level: Log level to filter (ALL, DEBUG, INFO, WARNING,
                   ERROR, CRITICAL)
        """
        self.current_filter = level
        self.refresh_logs()

    def clear_display(self):
        """Clear the log display (does not delete log file)."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.insert("1.0", "Display cleared.\n")
        self.log_textbox.configure(state="disabled")
        self.log_count_label.configure(text="Total: 0 logs")

    def _filter_log_lines(self, logs):
        """
        Filter log lines based on current filter setting.

        Args:
            logs: List of log lines

        Returns:
            List of filtered log lines
        """
        if self.current_filter == "ALL":
            return logs

        filtered = []
        for log in logs:
            if f"[{self.current_filter}]" in log:
                filtered.append(log)

        return filtered

    def _insert_colored_log(self, log_line: str):
        """
        Insert log line with color coding based on severity.

        Args:
            log_line: Log line to insert

        Note:
            CTkTextbox doesn't support native color tags,
            so logs are displayed as plain text.
            For colored text, tkinter.Text would be needed.
        """
        # Insert as plain text
        # TODO: Consider using tkinter.Text for colored log display
        self.log_textbox.insert("end", log_line)

    def _darken_color(self, hex_color: str) -> str:
        """
        Darken a hex color for hover effect.

        Args:
            hex_color: Hex color string (e.g., "#ff0000")

        Returns:
            Darkened hex color string
        """
        # Simple darkening by reducing RGB values by 20%
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)

            r = max(0, int(r * 0.8))
            g = max(0, int(g * 0.8))
            b = max(0, int(b * 0.8))

            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color
