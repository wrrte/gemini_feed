from abc import ABC, abstractmethod
from datetime import datetime

from database.schema.sensor import SensorType


class InterfaceSensor(ABC):
    """Abstract interface for sensor devices."""

    type: SensorType
    sensor_id: int
    coordinate_x: int
    coordinate_y: int
    created_at: datetime
    updated_at: datetime
    armed: bool
    detected: bool

    @abstractmethod
    def get_type(self):
        """Get the sensor type."""
        pass  # pragma: no cover

    @abstractmethod
    def intrude(self):
        """Simulate motion detection."""
        pass  # pragma: no cover

    @abstractmethod
    def release(self):
        """Clear motion detection."""
        pass  # pragma: no cover

    @abstractmethod
    def get_id(self):
        """Alias for getID."""
        pass  # pragma: no cover

    @abstractmethod
    def read(self):
        """Read the sensor state."""
        pass  # pragma: no cover

    @abstractmethod
    def arm(self):
        """Enable the sensor."""
        pass  # pragma: no cover

    @abstractmethod
    def disarm(self):
        """Disable the sensor."""
        pass  # pragma: no cover

    @abstractmethod
    def is_armed(self):
        """Check if the sensor is armed."""
        pass  # pragma: no cover
