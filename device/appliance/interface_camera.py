from abc import ABC, abstractmethod


class InterfaceCamera(ABC):
    """Abstract interface for camera devices."""

    @abstractmethod
    def set_id(self, id_):
        """Set the camera ID and load associated image."""
        pass  # pragma: no cover

    @abstractmethod
    def get_id(self):
        """Get the camera ID."""
        pass  # pragma: no cover

    @abstractmethod
    def get_view(self):
        """Get the current camera view as an image (PIL Image in Python)."""
        pass  # pragma: no cover

    @abstractmethod
    def pan_right(self):
        """Pan camera to the right. Returns True if successful."""
        pass  # pragma: no cover

    @abstractmethod
    def pan_left(self):
        """Pan camera to the left. Returns True if successful."""
        pass  # pragma: no cover

    @abstractmethod
    def zoom_in(self):
        """Zoom in. Returns True if successful."""
        pass  # pragma: no cover

    @abstractmethod
    def zoom_out(self):
        """Zoom out. Returns True if successful."""
        pass  # pragma: no cover
