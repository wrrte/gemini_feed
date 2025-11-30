from datetime import datetime
from unittest.mock import Mock

import pytest

from database.schema.sensor import SensorType
from device.sensor import create_sensor_from_schema
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
    schema.armed = False  # [수정] 기본값을 False로 명시적 설정
    return schema


def test_windoor_sensor_init():
    schema = create_mock_schema(SensorType.WINDOOR_SENSOR, sensor_id=99)
    sensor = WindowDoorSensor(schema)

    assert sensor.get_id() == 99
    assert sensor.get_type() == SensorType.WINDOOR_SENSOR
    assert not sensor.is_armed()


def test_windoor_sensor_invalid_type():
    """Test that AssertionError is raised for invalid sensor type."""
    schema = create_mock_schema(SensorType.MOTION_DETECTOR_SENSOR)

    # [수정] pytest.raises를 사용하여 예외 발생 검증 (assert False 제거)
    with pytest.raises(
        AssertionError,
        match="Sensor type must be WINDOOR_SENSOR"
    ):
        WindowDoorSensor(schema)


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


def test_create_sensor_from_schema_success():
    """Test factory function creates correct WindowDoorSensor instance."""
    schema = create_mock_schema(SensorType.WINDOOR_SENSOR)
    sensor = create_sensor_from_schema(schema)
    assert isinstance(sensor, WindowDoorSensor)
