from datetime import datetime
from unittest.mock import Mock

from database.schema.sensor import SensorType
from device.sensor.window_door_sensor import WindowDoorSensor


def create_mock_schema(sensor_type, sensor_id=1):
    schema = Mock()
    schema.sensor_type = sensor_type
    schema.sensor_id = sensor_id
    schema.coordinate_x = 0
    schema.coordinate_y = 0
    schema.zone_id = 1
    schema.created_at = datetime.now()
    schema.updated_at = datetime.now()
    return schema


def test_windoor_sensor_init():
    schema = create_mock_schema(SensorType.WINDOOR_SENSOR, sensor_id=99)
    sensor = WindowDoorSensor(schema)

    assert sensor.get_id() == 99
    assert sensor.get_type() == SensorType.WINDOOR_SENSOR
    assert not sensor.is_armed()


def test_windoor_sensor_invalid_type():
    schema = create_mock_schema(SensorType.MOTION_DETECTOR_SENSOR)

    try:
        WindowDoorSensor(schema)
        assert False, "Should raise AssertionError for invalid sensor type"
    except AssertionError as e:
        assert str(e) == "Sensor type must be WINDOOR_SENSOR"


def test_windoor_sensor_detection_logic():
    schema = create_mock_schema(SensorType.WINDOOR_SENSOR)
    sensor = WindowDoorSensor(schema)

    sensor.arm()
    assert sensor.is_armed()

    sensor.intrude()
    assert sensor.read() is True

    sensor.release()
    assert sensor.read() is False

    sensor.disarm()
    assert not sensor.is_armed()


def test_windoor_sensor_detection_disarmed():
    schema = create_mock_schema(SensorType.WINDOOR_SENSOR)
    sensor = WindowDoorSensor(schema)

    sensor.disarm()

    sensor.intrude()

    assert sensor.read() is False
