from abc import ABC, abstractmethod

import customtkinter as ctk


class PageMixin(ABC):
    """
    모든 페이지(내부 프레임, 외부 창)가 공통으로 가지는 기능 정의
    """

    def __init__(self, page_id: str):
        self.id = page_id

    @abstractmethod
    def draw_page(self):
        """
        페이지의 UI 요소를 그리는 메서드입니다.
        자식 클래스에서 반드시 구현해야 합니다.
        """
        pass

    def get_id(self) -> str:
        """페이지의 ID를 반환합니다."""
        return self.id

    def set_id(self, page_id: str):
        """페이지의 ID를 설정합니다."""
        self.id = page_id


class InterfacePage(ctk.CTkFrame, PageMixin):
    """
    메인 앱 내부에 포함되는 페이지 (Frame 기반)
    """

    def __init__(self, master, page_id: str, **kwargs):
        # CTkFrame 초기화
        ctk.CTkFrame.__init__(self, master, **kwargs)
        # PageMixin 초기화
        PageMixin.__init__(self, page_id)


class InterfaceWindow(ctk.CTkToplevel, PageMixin):
    """
    별도의 창으로 뜨는 페이지 (Toplevel 기반)
    """

    def __init__(
            self,
            master,
            page_id: str,
            title: str = "SafeHome Window",
            initially_hidden: bool = True,
            window_width: int = 400,
            window_height: int = 300,
            **kwargs):
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
