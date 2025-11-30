from datetime import datetime
from unittest.mock import Mock

from database.schema.sensor import SensorType
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
    schema = create_mock_schema(SensorType.WINDOOR_SENSOR)

    try:
        MotionDetectorSensor(schema)
        assert False, "Should raise AssertionError for invalid sensor type"
    except AssertionError as e:
        assert str(e) == "Sensor type must be MOTION_DETECTOR_SENSOR"


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
