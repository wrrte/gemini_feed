from abc import ABC, abstractmethod


class InterfaceAlarm(ABC):
    """Abstract interface for alarm devices."""

    @abstractmethod
    def get_id(self):
        """Get the alarm ID."""
        pass

    @abstractmethod
    def set_id(self, id_):
        """Set the alarm ID."""
        pass

    @abstractmethod
    def get_location(self):
        """Get the alarm location (x, y coordinates)."""
        pass

    @abstractmethod
    def ring_alarm(self):
        """Activate the alarm to ring."""
        pass

    @abstractmethod
    def stop_alarm(self):
        """Stop the alarm from ringing."""
        pass

    @abstractmethod
    def is_ringing(self):
        """Check whether the alarm is currently ringing.
        Returns True if ringing, False otherwise."""
        pass

    @abstractmethod
    def get_info(self):
        """Get alarm hardware & current status information."""
        pass
