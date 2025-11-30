import threading
import time

from .interface_alarm import InterfaceAlarm

ALARM_DURATION = 60  # Duration (seconds) that alarm rings


class Alarm(threading.Thread, InterfaceAlarm):
    """
    Alarm class connects the system and alarm hardware device.
    It is the device driver of alarm hardware.
    """

    def __init__(self):
        super().__init__(daemon=True)

        self.alarm_id = 0
        self.x = 0
        self.y = 0
        self.ringing = False
        self._running = True
        self._lock = threading.RLock()
        self.ring_start_time = None

        self.start()

    def set_id(self, alarm_id):
        """Set the alarm ID."""
        with self._lock:
            if not isinstance(alarm_id, int):
                return False
            self.alarm_id = alarm_id
            return True

    def get_id(self):
        """Get the alarm ID."""
        return self.alarm_id

    def get_location(self):
        """Get the alarm location (x, y coordinates)."""
        with self._lock:
            return (self.x, self.y)

    def ring_alarm(self):
        """Activate the alarm to ring."""
        with self._lock:
            if not self.ringing:
                self.ringing = True
                self.ring_start_time = time.time()
                print(f"[Alarm {self.alarm_id}] ringing started!")

    def stop_alarm(self):
        """Stop the alarm from ringing."""
        with self._lock:
            if self.ringing:
                self.ringing = False
                duration = (
                    time.time() - self.ring_start_time
                    if self.ring_start_time
                    else 0
                )
                print(f"[Alarm {self.alarm_id}] ringing stopped")
                print(f"(rang for {duration:.1f} seconds)")
                self.ring_start_time = None

    def is_ringing(self):
        """Check whether the alarm is currently ringing."""
        with self._lock:
            return self.ringing

    def get_info(self):
        """Get alarm hardware & current status information."""
        with self._lock:
            status = "RINGING" if self.ringing else "SILENT"

            return {
                "alarm_id": self.alarm_id,
                "status": status,
                "ringing": self.ringing,
            }

    def run(self):
        """Thread loop for alarm operations."""
        while self._running:
            # Simulate alarm hardware polling/operations
            time.sleep(0.1)

            # Auto-stop after a certain duration
            with self._lock:
                if self.ringing and self.ring_start_time:
                    if time.time() - self.ring_start_time > ALARM_DURATION:
                        self.stop_alarm()

    def shutdown(self):
        """Shutdown the alarm thread."""
        self._running = False
        self.stop_alarm()
