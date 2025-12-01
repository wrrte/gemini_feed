"""
Add a new sensor, Remove a sensor is out of scope.
"""

import os
import sys
import threading
import time
from typing import Callable, Dict, List, Optional, Tuple

from database.schema.sensor import SensorSchema, SensorType
from device.sensor.interface_sensor import InterfaceSensor
from manager.log_manager import LogManager

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
sys.path.append(src_dir)


class SensorManager:
    """
    SensorManager class to manage sensors.

    Responsibilities:
    """

    def __init__(
        self,
        sensor_dict: dict[int, InterfaceSensor] = {},
        log_manager: Optional[LogManager] = None,
        external_call: Optional[Callable[[], List[str]]] = None,
        handle_intrusion: Optional[Callable[[int, SensorType], None]] = None,
    ):
        """
        Initialize the SensorManager.
        """
        # managers & services
        self.log_manager = log_manager
        self.external_call = external_call
        self.handle_intrusion = handle_intrusion

        # initialize sensors
        self.sensor_dict = {}
        self.sensor_ids = []
        for sensor_id, sensor in sensor_dict.items():
            self.sensor_dict[sensor_id] = sensor
            self.sensor_ids.append(sensor_id)

        # for asynchronous monitoring
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitor_lock = threading.Lock()
        self._monitoring_active = False
        self._monitor_interval = 1.0

    def get_sensor(self, id) -> InterfaceSensor:
        """
        Get the sensor dictionary.
        """
        return self.sensor_dict[id]

    def add_sensor(self, id, sensor):
        """
        Add a sensor to the sensor manager.
        """
        # NOTE: This part is for next iteration
        raise NotImplementedError("Adding sensors is not implemented.")

    def remove_sensor(self, sensor_id):
        """
        Remove a sensor from the sensor manager.
        """
        # NOTE: This part is for next iteration
        raise NotImplementedError("Removing sensors is not implemented.")

    def arm_sensors(self, sensor_ids):
        """
        Arm multiple sensors by their IDs.
        Thread-safe with monitoring loop.
        """
        with self._monitor_lock:
            for sensor_id in sensor_ids:
                if sensor_id in self.sensor_dict:
                    self.sensor_dict[sensor_id].arm()

        return True

    def disarm_sensors(self, sensor_ids):
        """
        Disarm multiple sensors by their IDs.
        Thread-safe with monitoring loop.
        """
        with self._monitor_lock:
            for sensor_id in sensor_ids:
                if sensor_id in self.sensor_dict:
                    self.sensor_dict[sensor_id].disarm()

        return True

    def arm_all_sensors(self):
        """
        Arm all sensors.
        """
        for sensor in self.sensor_dict.values():
            sensor.arm()

        return True

    def disarm_all_sensors(self):
        """
        Disarm all sensors.
        """
        for sensor in self.sensor_dict.values():
            sensor.disarm()

        return True

    def arm_sensor(self, sensor_id):
        """
        Arm a single sensor by its ID.
        Thread-safe with monitoring loop.
        """
        with self._monitor_lock:
            if sensor_id in self.sensor_dict:
                self.sensor_dict[sensor_id].arm()
                return True

        return False

    def disarm_sensor(self, sensor_id):
        """
        Disarm a single sensor by its ID.
        Thread-safe with monitoring loop.
        """
        with self._monitor_lock:
            if sensor_id in self.sensor_dict:
                self.sensor_dict[sensor_id].disarm()
                return True

        return False

    def intrude_sensor(self, sensor_id):
        """
        Simulate intrusion on a sensor by its ID.
        Thread-safe with monitoring loop.
        """
        with self._monitor_lock:
            if sensor_id in self.sensor_dict:
                self.sensor_dict[sensor_id].intrude()
                return True

        return False

    def release_sensor(self, sensor_id):
        """
        Release (clear) intrusion state on a sensor by its ID.
        Thread-safe with monitoring loop.
        """
        with self._monitor_lock:
            if sensor_id in self.sensor_dict:
                self.sensor_dict[sensor_id].release()
                return True

        return False

    def read_sensor(self, sensor_id) -> bool:
        """
        Read the intrusion state of a sensor by its ID.
        """
        with self._monitor_lock:
            if sensor_id in self.sensor_dict:
                return self.sensor_dict[sensor_id].read()
        return False

    def get_coordinates(self, sensor_id) -> Optional[Tuple[int, int]]:
        """
        Get the coordinates of a sensor by its ID.
        """
        if sensor_id in self.sensor_dict:
            return (
                self.sensor_dict[sensor_id].coordinate_x,
                self.sensor_dict[sensor_id].coordinate_y,
            )

        return None

    def move_sensor(self, sensor_id, new_coordinates: Tuple[int, int]):
        """
        Move a sensor to new coordinates.

        :param new_coordinates: [x, y]
        """
        if sensor_id in self.sensor_dict:
            self.sensor_dict[sensor_id].coordinate_x = new_coordinates[0]
            self.sensor_dict[sensor_id].coordinate_y = new_coordinates[1]
            return True

        return False

    def get_all_sensor_info(self) -> Dict[int, SensorSchema]:
        """
        Get information of all sensors.
        """
        info = {}
        for sensor_id, sensor in self.sensor_dict.items():
            info[sensor_id] = SensorSchema(
                sensor_id=sensor.sensor_id,
                sensor_type=sensor.get_type(),
                coordinate_x=sensor.coordinate_x,
                coordinate_y=sensor.coordinate_y,
                coordinate_x2=getattr(sensor, "coordinate_x2", None),
                coordinate_y2=getattr(sensor, "coordinate_y2", None),
                created_at=sensor.created_at,
                updated_at=sensor.updated_at,
            )
        return info

    def if_intrusion_detected(self):
        """
        Check if any sensor has detected an intrusion.
        """
        for sensor in self.sensor_dict.values():
            if sensor.read():
                return True
        return False

    def start_monitoring(self):
        """
        Start sensor monitoring in a background thread.
        It does not block the main thread.
        """
        if self._monitoring_active:
            print("[SensorMonitor] Monitoring is already active")
            return

        self._monitoring_active = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_sensors_loop,
            daemon=True,  # auto-terminate when main program exits
            name="SensorMonitorThread",
        )
        self._monitor_thread.start()

    def stop_monitoring(self):
        """
        Stop sensor monitoring.
        """
        if not self._monitoring_active:
            print("Sensor monitoring is not active")
            return

        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
        print("Sensor monitoring stopped")

    def _monitor_sensors_loop(self):
        """
        Background thread for sensor monitoring loop.
        Check all sensors periodically and handle intrusion detection.
        """
        while self._monitoring_active:
            try:
                # use lock to safely access the sensor dictionary
                with self._monitor_lock:
                    self._check_all_sensors()

                # wait for the next check
                time.sleep(self._monitor_interval)

            except Exception as e:
                print(f"[SensorMonitor] Error in monitoring loop: {e}")
                if self.log_manager:
                    self.log_manager.error(f"Sensor monitoring error: {e}")
                time.sleep(self._monitor_interval)

    def _check_all_sensors(self):
        """
        Check all sensors and handle intrusion detection.
        This method is called in a background thread.
        """
        for sensor_id, sensor in self.sensor_dict.items():
            # if the sensor is armed and intrusion is detected
            if sensor.is_armed() and sensor.read():
                self.handle_intrusion(sensor_id, sensor.get_type())


if __name__ == "__main__":  # pragma: no cover
    sensor_manager = SensorManager()
    sensor_manager.arm_all_sensors()
    all_info = sensor_manager.get_all_sensor_info()
    for sensor_id, info in all_info.items():
        print(
            f"Sensor ID: {sensor_id}, Type: {info['type']}, \
                Armed: {info['armed']}, State: {info['state']}"
        )