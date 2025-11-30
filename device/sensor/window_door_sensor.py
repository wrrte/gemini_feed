from database.schema.sensor import SensorSchema, SensorType
from device.sensor.interface_sensor import InterfaceSensor


class WindowDoorSensor(InterfaceSensor):
    """
    Window/door sensor class representing a window/door sensor device.
    """

    def __init__(
        self,
        sensor_schema: SensorSchema,
    ):
        self.sensor_type = sensor_schema.sensor_type
        self.sensor_id = sensor_schema.sensor_id
        self.coordinate_x = sensor_schema.coordinate_x
        self.coordinate_y = sensor_schema.coordinate_y
        self.coordinate_x2 = None
        self.coordinate_y2 = None
        self.created_at = sensor_schema.created_at
        self.updated_at = sensor_schema.updated_at
        self.armed = sensor_schema.armed
        self.detected = False

        assert self.sensor_type == SensorType.WINDOOR_SENSOR, (
            "Sensor type must be WINDOOR_SENSOR"
        )

    def get_type(self):
        """Get the sensor type."""
        return self.sensor_type

    def intrude(self):
        """Simulate motion detection."""
        self.detected = True

    def release(self):
        """Clear motion detection."""
        self.detected = False

    def get_id(self):
        """Alias for getID."""
        return self.sensor_id

    def read(self):
        """Read the sensor state."""
        if self.armed:
            return self.detected
        return False

    def arm(self):
        """Enable the sensor."""
        self.armed = True

    def disarm(self):
        """Disable the sensor."""
        self.armed = False

    def is_armed(self):
        """Test if the sensor is enabled."""
        return self.armed
