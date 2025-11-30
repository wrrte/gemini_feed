from database.schema.sensor import SensorSchema, SensorType
from device.sensor.interface_sensor import InterfaceSensor
from device.sensor.motion_detector_sensor import MotionDetectorSensor
from device.sensor.window_door_sensor import WindowDoorSensor

__all__ = [
    "InterfaceSensor",
    "DoorSensor",
    "WindowDoorSensor",
    "MotionDetectorSensor",
    "create_sensor_from_schema",
]


def create_sensor_from_schema(sensor_schema: SensorSchema) -> InterfaceSensor:
    """
    Factory function to create appropriate sensor instance from schema.

    Args:
        sensor_schema: SensorSchema object containing sensor data

    Returns:
        InterfaceSensor: Concrete sensor instance based on sensor type

    Raises:
        ValueError: If sensor type is unknown
    """
    sensor_type_map = {
        SensorType.WINDOOR_SENSOR: WindowDoorSensor,
        SensorType.MOTION_DETECTOR_SENSOR: MotionDetectorSensor,
    }

    sensor_class = sensor_type_map.get(sensor_schema.sensor_type)
    if sensor_class is None:
        raise ValueError(f"Unknown sensor type: {sensor_schema.sensor_type}")

    return sensor_class(sensor_schema)
