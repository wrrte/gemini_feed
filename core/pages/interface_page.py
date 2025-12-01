from abc import ABC, abstractmethod

import customtkinter as ctk


class PageMixin(ABC):
    """
    Common functionality for all pages (internal frames, external windows)
    """

    def __init__(self, page_id: str):
        self.id = page_id

    @abstractmethod
    def draw_page(self):
        """
        Draw the UI elements of the page.
        Must be implemented by child classes.
        """
        pass  # pragma: no cover

    def get_id(self) -> str:
        """Return the ID of the page."""
        return self.id

    def set_id(self, page_id: str):
        """Set the ID of the page."""
        self.id = page_id


class InterfacePage(ctk.CTkFrame, PageMixin):
    """
    Page included inside the main app (Frame-based)
    """

    def __init__(self, master, page_id: str, **kwargs):
        # Initialize CTkFrame
        ctk.CTkFrame.__init__(self, master, **kwargs)
        # Initialize PageMixin
        PageMixin.__init__(self, page_id)


class InterfaceWindow(ctk.CTkToplevel, PageMixin):
    """
    Page that appears as a separate window (Toplevel-based)
    """

    def __init__(
        self,
        master,
        page_id: str,
        title: str = "SafeHome Window",
        initially_hidden: bool = True,
        window_width: int = 400,
        window_height: int = 300,
        **kwargs,
    ):
        # initialize CTkToplevel
        ctk.CTkToplevel.__init__(self, master, **kwargs)
        # initially hidden
        if initially_hidden:
            self.withdraw()
        # initialize PageMixin
        PageMixin.__init__(self, page_id)
        # set title
        self.title(title)
        # set geometry
        self.geometry(f"{window_width}x{window_height}")
