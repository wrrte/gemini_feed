from datetime import datetime
from unittest.mock import Mock

import pytest  # pytest 임포트 확인

from database.schema.sensor import SensorType
from device.sensor import create_sensor_from_schema
from device.sensor.motion_detector_sensor import MotionDetectorSensor


def create_mock_schema(sensor_type, sensor_id=1):
    schema = Mock()
    schema.sensor_type = sensor_type
    schema.sensor_id = sensor_id
    schema.coordinate_x = 10
    schema.coordinate_y = 20
    schema.zone_id = 5
    schema.created_at = datetime.now()
    schema.updated_at = datetime.now()
    schema.armed = False
    return schema


def test_motion_detector_init():
    schema = create_mock_schema(
        SensorType.MOTION_DETECTOR_SENSOR, sensor_id=10
    )
    sensor = MotionDetectorSensor(schema)

    assert sensor.get_id() == 10
    assert sensor.get_type() == SensorType.MOTION_DETECTOR_SENSOR
    assert sensor.coordinate_x == 10
    assert not sensor.is_armed()


def test_motion_detector_invalid_type():
    """Test that AssertionError is raised for invalid sensor type."""
    schema = create_mock_schema(SensorType.WINDOOR_SENSOR)

    with pytest.raises(
        AssertionError,
        match="Sensor type must be MOTION_DETECTOR_SENSOR"
    ):
        MotionDetectorSensor(schema)


def test_motion_detector_arming():
    schema = create_mock_schema(SensorType.MOTION_DETECTOR_SENSOR)
    sensor = MotionDetectorSensor(schema)

    assert not sensor.is_armed()

    sensor.arm()
    assert sensor.is_armed()

    sensor.disarm()
    assert not sensor.is_armed()


def test_motion_detector_detection_logic():
    schema = create_mock_schema(SensorType.MOTION_DETECTOR_SENSOR)
    sensor = MotionDetectorSensor(schema)

    sensor.arm()
    assert not sensor.read()

    sensor.intrude()
    assert sensor.read() is True

    sensor.release()
    assert sensor.read() is False


def test_motion_detector_read_detection_disarmed():
    schema = create_mock_schema(SensorType.MOTION_DETECTOR_SENSOR)
    sensor = MotionDetectorSensor(schema)

    sensor.disarm()
    sensor.intrude()

    assert sensor.read() is False

    sensor.arm()
    assert sensor.read() is True


def test_create_sensor_from_schema_success():
    """Test factory function creates correct instance."""
    schema = create_mock_schema(SensorType.MOTION_DETECTOR_SENSOR)
    sensor = create_sensor_from_schema(schema)
    assert isinstance(sensor, MotionDetectorSensor)


def test_create_sensor_from_schema_invalid():
    """Test factory function raises error for unknown type."""
    schema = create_mock_schema("UNKNOWN_TYPE")

    with pytest.raises(ValueError, match="Unknown sensor type"):
        create_sensor_from_schema(schema)
