"""
Integration Test: SensorManager + WindowDoorSensor + MotionDetectorSensor

Tests the interaction between SensorManager and actual sensor devices.
Verifies arm/disarm, intrusion detection, and sensor state management.
"""

from datetime import datetime

import pytest

from database.schema.sensor import SensorSchema, SensorType
from device.sensor.motion_detector_sensor import MotionDetectorSensor
from device.sensor.window_door_sensor import WindowDoorSensor
from manager.sensor_manager import SensorManager

# ==================== Fixtures ====================


@pytest.fixture
def window_door_sensor_schema():
    """Create a WindowDoorSensor schema for testing."""
    return SensorSchema(
        sensor_id=1,
        sensor_type=SensorType.WINDOOR_SENSOR,
        coordinate_x=100,
        coordinate_y=200,
        coordinate_x2=None,
        coordinate_y2=None,
        armed=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def motion_detector_sensor_schema():
    """Create a MotionDetectorSensor schema for testing."""
    return SensorSchema(
        sensor_id=2,
        sensor_type=SensorType.MOTION_DETECTOR_SENSOR,
        coordinate_x=150,
        coordinate_y=250,
        coordinate_x2=200,
        coordinate_y2=300,
        armed=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def window_door_sensor(window_door_sensor_schema):
    """Create a real WindowDoorSensor instance."""
    return WindowDoorSensor(window_door_sensor_schema)


@pytest.fixture
def motion_detector_sensor(motion_detector_sensor_schema):
    """Create a real MotionDetectorSensor instance."""
    return MotionDetectorSensor(motion_detector_sensor_schema)


@pytest.fixture
def sensor_manager_with_sensors(window_door_sensor, motion_detector_sensor):
    """Create SensorManager with real sensor instances."""
    sensor_dict = {
        1: window_door_sensor,
        2: motion_detector_sensor,
    }
    return SensorManager(sensor_dict=sensor_dict)


@pytest.fixture
def sensor_manager_empty():
    """Create an empty SensorManager."""
    return SensorManager()


# ==================== Arm/Disarm Integration Tests ====================


def test_sensor_manager_arm_single_windoor_sensor(sensor_manager_with_sensors):
    """Test arming a single window/door sensor through manager."""
    # Arrange
    sensor_id = 1

    # Act
    result = sensor_manager_with_sensors.arm_sensor(sensor_id)

    # Assert
    assert result is True
    sensor = sensor_manager_with_sensors.get_sensor(sensor_id)
    assert sensor.is_armed() is True


def test_sensor_manager_arm_single_motion_detector(
    sensor_manager_with_sensors,
):
    """Test arming a single motion detector sensor through manager."""
    # Arrange
    sensor_id = 2

    # Act
    result = sensor_manager_with_sensors.arm_sensor(sensor_id)

    # Assert
    assert result is True
    sensor = sensor_manager_with_sensors.get_sensor(sensor_id)
    assert sensor.is_armed() is True


def test_sensor_manager_disarm_single_sensor(sensor_manager_with_sensors):
    """Test disarming a single sensor through manager."""
    # Arrange
    sensor_id = 1
    sensor_manager_with_sensors.arm_sensor(sensor_id)

    # Act
    result = sensor_manager_with_sensors.disarm_sensor(sensor_id)

    # Assert
    assert result is True
    sensor = sensor_manager_with_sensors.get_sensor(sensor_id)
    assert sensor.is_armed() is False


def test_sensor_manager_arm_all_sensors(sensor_manager_with_sensors):
    """Test arming all sensors at once."""
    # Act
    result = sensor_manager_with_sensors.arm_all_sensors()

    # Assert
    assert result is True
    assert sensor_manager_with_sensors.get_sensor(1).is_armed() is True
    assert sensor_manager_with_sensors.get_sensor(2).is_armed() is True


def test_sensor_manager_disarm_all_sensors(sensor_manager_with_sensors):
    """Test disarming all sensors at once."""
    # Arrange
    sensor_manager_with_sensors.arm_all_sensors()

    # Act
    result = sensor_manager_with_sensors.disarm_all_sensors()

    # Assert
    assert result is True
    assert sensor_manager_with_sensors.get_sensor(1).is_armed() is False
    assert sensor_manager_with_sensors.get_sensor(2).is_armed() is False


def test_sensor_manager_arm_multiple_sensors(sensor_manager_with_sensors):
    """Test arming multiple specific sensors."""
    # Act
    result = sensor_manager_with_sensors.arm_sensors([1, 2])

    # Assert
    assert result is True
    assert sensor_manager_with_sensors.get_sensor(1).is_armed() is True
    assert sensor_manager_with_sensors.get_sensor(2).is_armed() is True


def test_sensor_manager_disarm_multiple_sensors(sensor_manager_with_sensors):
    """Test disarming multiple specific sensors."""
    # Arrange
    sensor_manager_with_sensors.arm_all_sensors()

    # Act
    result = sensor_manager_with_sensors.disarm_sensors([1, 2])

    # Assert
    assert result is True
    assert sensor_manager_with_sensors.get_sensor(1).is_armed() is False
    assert sensor_manager_with_sensors.get_sensor(2).is_armed() is False


def test_sensor_manager_arm_nonexistent_sensor(sensor_manager_with_sensors):
    """Test arming a non-existent sensor returns False."""
    # Act
    result = sensor_manager_with_sensors.arm_sensor(999)

    # Assert
    assert result is False


def test_sensor_manager_disarm_nonexistent_sensor(sensor_manager_with_sensors):
    """Test disarming a non-existent sensor returns False."""
    # Act
    result = sensor_manager_with_sensors.disarm_sensor(999)

    # Assert
    assert result is False


# ==================== Intrusion Detection Integration Tests ==================


def test_sensor_manager_intrude_armed_windoor_sensor(
    sensor_manager_with_sensors,
):
    """Test intrusion detection on armed window/door sensor."""
    # Arrange
    sensor_id = 1
    sensor_manager_with_sensors.arm_sensor(sensor_id)

    # Act
    result = sensor_manager_with_sensors.intrude_sensor(sensor_id)

    # Assert
    assert result is True
    assert sensor_manager_with_sensors.read_sensor(sensor_id) is True


def test_sensor_manager_intrude_armed_motion_detector(
    sensor_manager_with_sensors,
):
    """Test intrusion detection on armed motion detector sensor."""
    # Arrange
    sensor_id = 2
    sensor_manager_with_sensors.arm_sensor(sensor_id)

    # Act
    result = sensor_manager_with_sensors.intrude_sensor(sensor_id)

    # Assert
    assert result is True
    assert sensor_manager_with_sensors.read_sensor(sensor_id) is True


def test_sensor_manager_intrude_disarmed_sensor_no_detection(
    sensor_manager_with_sensors,
):
    """Test that disarmed sensor does not report intrusion."""
    # Arrange
    sensor_id = 1
    # Sensor is disarmed by default

    # Act
    sensor_manager_with_sensors.intrude_sensor(sensor_id)

    # Assert - disarmed sensor should not report intrusion
    assert sensor_manager_with_sensors.read_sensor(sensor_id) is False


def test_sensor_manager_release_sensor(sensor_manager_with_sensors):
    """Test releasing intrusion state on a sensor."""
    # Arrange
    sensor_id = 1
    sensor_manager_with_sensors.arm_sensor(sensor_id)
    sensor_manager_with_sensors.intrude_sensor(sensor_id)

    # Act
    result = sensor_manager_with_sensors.release_sensor(sensor_id)

    # Assert
    assert result is True
    assert sensor_manager_with_sensors.read_sensor(sensor_id) is False


def test_sensor_manager_if_intrusion_detected_true(
    sensor_manager_with_sensors,
):
    """Test if_intrusion_detected returns True when intrusion exists."""
    # Arrange
    sensor_manager_with_sensors.arm_sensor(1)
    sensor_manager_with_sensors.intrude_sensor(1)

    # Act & Assert
    assert sensor_manager_with_sensors.if_intrusion_detected() is True


def test_sensor_manager_if_intrusion_detected_false(
    sensor_manager_with_sensors,
):
    """Test if_intrusion_detected returns False when no intrusion."""
    # Arrange - all sensors disarmed and no intrusion

    # Act & Assert
    assert sensor_manager_with_sensors.if_intrusion_detected() is False


def test_sensor_manager_intrude_nonexistent_sensor(
    sensor_manager_with_sensors,
):
    """Test intruding a non-existent sensor returns False."""
    # Act
    result = sensor_manager_with_sensors.intrude_sensor(999)

    # Assert
    assert result is False


def test_sensor_manager_release_nonexistent_sensor(
    sensor_manager_with_sensors,
):
    """Test releasing a non-existent sensor returns False."""
    # Act
    result = sensor_manager_with_sensors.release_sensor(999)

    # Assert
    assert result is False


def test_sensor_manager_read_nonexistent_sensor(sensor_manager_with_sensors):
    """Test reading a non-existent sensor returns False."""
    # Act
    result = sensor_manager_with_sensors.read_sensor(999)

    # Assert
    assert result is False


# ==================== Sensor Info Integration Tests ====================


def test_sensor_manager_get_all_sensor_info(sensor_manager_with_sensors):
    """Test getting info of all sensors."""
    # Act
    info = sensor_manager_with_sensors.get_all_sensor_info()

    # Assert
    assert len(info) == 2
    assert 1 in info
    assert 2 in info
    assert info[1].sensor_type == SensorType.WINDOOR_SENSOR
    assert info[2].sensor_type == SensorType.MOTION_DETECTOR_SENSOR


def test_sensor_manager_get_coordinates(sensor_manager_with_sensors):
    """Test getting sensor coordinates."""
    # Act
    coords = sensor_manager_with_sensors.get_coordinates(1)

    # Assert
    assert coords == (100, 200)


def test_sensor_manager_get_coordinates_nonexistent(
    sensor_manager_with_sensors,
):
    """Test getting coordinates of non-existent sensor."""
    # Act
    coords = sensor_manager_with_sensors.get_coordinates(999)

    # Assert
    assert coords is None


def test_sensor_manager_move_sensor(sensor_manager_with_sensors):
    """Test moving a sensor to new coordinates."""
    # Arrange
    new_coords = (300, 400)

    # Act
    result = sensor_manager_with_sensors.move_sensor(1, new_coords)

    # Assert
    assert result is True
    assert sensor_manager_with_sensors.get_coordinates(1) == new_coords


def test_sensor_manager_move_nonexistent_sensor(sensor_manager_with_sensors):
    """Test moving a non-existent sensor returns False."""
    # Act
    result = sensor_manager_with_sensors.move_sensor(999, (100, 100))

    # Assert
    assert result is False


# ==================== Edge Cases ====================


def test_sensor_manager_arm_sensors_with_invalid_ids(
    sensor_manager_with_sensors,
):
    """Test arming with list containing invalid sensor IDs."""
    # Act - should silently skip invalid IDs
    result = sensor_manager_with_sensors.arm_sensors([1, 999])

    # Assert
    assert result is True
    assert sensor_manager_with_sensors.get_sensor(1).is_armed() is True


def test_sensor_manager_disarm_sensors_with_invalid_ids(
    sensor_manager_with_sensors,
):
    """Test disarming with list containing invalid sensor IDs."""
    # Arrange
    sensor_manager_with_sensors.arm_all_sensors()

    # Act - should silently skip invalid IDs
    result = sensor_manager_with_sensors.disarm_sensors([1, 999])

    # Assert
    assert result is True
    assert sensor_manager_with_sensors.get_sensor(1).is_armed() is False


def test_sensor_manager_empty_sensor_dict(sensor_manager_empty):
    """Test operations on empty sensor manager."""
    # Act & Assert
    assert sensor_manager_empty.if_intrusion_detected() is False
    assert sensor_manager_empty.get_all_sensor_info() == {}
    assert sensor_manager_empty.arm_all_sensors() is True
    assert sensor_manager_empty.disarm_all_sensors() is True


def test_windoor_sensor_type_validation(window_door_sensor):
    """Test that WindowDoorSensor returns correct type."""
    assert window_door_sensor.get_type() == SensorType.WINDOOR_SENSOR


def test_motion_detector_sensor_type_validation(motion_detector_sensor):
    """Test that MotionDetectorSensor returns correct type."""
    assert (
        motion_detector_sensor.get_type() == SensorType.MOTION_DETECTOR_SENSOR
    )


def test_sensor_manager_get_sensor(sensor_manager_with_sensors):
    """Test getting a specific sensor by ID."""
    # Act
    sensor = sensor_manager_with_sensors.get_sensor(1)

    # Assert
    assert sensor is not None
    assert sensor.get_id() == 1
