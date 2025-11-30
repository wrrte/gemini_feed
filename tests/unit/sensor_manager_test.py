from datetime import datetime

import pytest

from database.schema.sensor import SensorSchema, SensorType
from device.sensor import create_sensor_from_schema
from manager.sensor_manager import SensorManager


@pytest.fixture
def sample_sensors():
    """Create sample sensor schemas for testing."""
    return [
        SensorSchema(
            sensor_id=1,
            sensor_type=SensorType.WINDOOR_SENSOR,
            coordinate_x=100,
            coordinate_y=50,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        SensorSchema(
            sensor_id=2,
            sensor_type=SensorType.WINDOOR_SENSOR,
            coordinate_x=200,
            coordinate_y=100,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        SensorSchema(
            sensor_id=3,
            sensor_type=SensorType.MOTION_DETECTOR_SENSOR,
            coordinate_x=150,
            coordinate_y=75,
            coordinate_x2=200,
            coordinate_y2=100,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]


@pytest.fixture
def sensor_manager(sample_sensors):
    """Create a SensorManager with sample sensors."""
    sensor_dict = {
        sensor.sensor_id: create_sensor_from_schema(sensor)
        for sensor in sample_sensors
    }
    return SensorManager(sensor_dict)


def test_sensor_manager_initialization(sensor_manager):
    """Test SensorManager initialization."""
    assert len(sensor_manager.sensor_dict) == 3
    assert sensor_manager.sensor_ids == [1, 2, 3]
    assert 1 in sensor_manager.sensor_dict
    assert 2 in sensor_manager.sensor_dict
    assert 3 in sensor_manager.sensor_dict


def test_arm_single_sensor(sensor_manager):
    """Test arming a single sensor."""
    assert sensor_manager.arm_sensor(1) is True
    assert sensor_manager.sensor_dict[1].is_armed() is True
    assert sensor_manager.sensor_dict[2].is_armed() is False
    assert sensor_manager.sensor_dict[3].is_armed() is False


def test_disarm_single_sensor(sensor_manager):
    """Test disarming a single sensor."""
    # First arm the sensor
    sensor_manager.arm_sensor(1)
    assert sensor_manager.sensor_dict[1].is_armed() is True

    # Then disarm it
    assert sensor_manager.disarm_sensor(1) is True
    assert sensor_manager.sensor_dict[1].is_armed() is False


def test_arm_nonexistent_sensor(sensor_manager):
    """Test arming a nonexistent sensor returns False."""
    assert sensor_manager.arm_sensor(999) is False


def test_disarm_nonexistent_sensor(sensor_manager):
    """Test disarming a nonexistent sensor returns False."""
    assert sensor_manager.disarm_sensor(999) is False


def test_arm_multiple_sensors(sensor_manager):
    """Test arming multiple sensors."""
    assert sensor_manager.arm_sensors([1, 2]) is True
    assert sensor_manager.sensor_dict[1].is_armed() is True
    assert sensor_manager.sensor_dict[2].is_armed() is True
    assert sensor_manager.sensor_dict[3].is_armed() is False


def test_disarm_multiple_sensors(sensor_manager):
    """Test disarming multiple sensors."""
    # First arm all sensors
    sensor_manager.arm_all_sensors()

    # Then disarm specific ones
    assert sensor_manager.disarm_sensors([1, 3]) is True
    assert sensor_manager.sensor_dict[1].is_armed() is False
    assert sensor_manager.sensor_dict[2].is_armed() is True
    assert sensor_manager.sensor_dict[3].is_armed() is False


def test_arm_all_sensors(sensor_manager):
    """Test arming all sensors."""
    assert sensor_manager.arm_all_sensors() is True
    assert sensor_manager.sensor_dict[1].is_armed() is True
    assert sensor_manager.sensor_dict[2].is_armed() is True
    assert sensor_manager.sensor_dict[3].is_armed() is True


def test_disarm_all_sensors(sensor_manager):
    """Test disarming all sensors."""
    # First arm all sensors
    sensor_manager.arm_all_sensors()

    # Then disarm all
    assert sensor_manager.disarm_all_sensors() is True
    assert sensor_manager.sensor_dict[1].is_armed() is False
    assert sensor_manager.sensor_dict[2].is_armed() is False
    assert sensor_manager.sensor_dict[3].is_armed() is False


def test_read_sensor_disarmed(sensor_manager):
    """Test reading a disarmed sensor returns False."""
    sensor_manager.sensor_dict[1].intrude()
    result = sensor_manager.read_sensor(1)
    assert result is False


def test_read_sensor_armed_no_intrusion(sensor_manager):
    """Test reading an armed sensor with no intrusion."""
    sensor_manager.arm_sensor(1)
    result = sensor_manager.read_sensor(1)
    assert result is False


def test_read_sensor_armed_with_intrusion(sensor_manager):
    """Test reading an armed sensor with intrusion detected."""
    sensor_manager.arm_sensor(1)
    sensor_manager.sensor_dict[1].intrude()
    result = sensor_manager.read_sensor(1)
    assert result is True


def test_read_nonexistent_sensor(sensor_manager):
    """Test reading a nonexistent sensor returns False."""
    result = sensor_manager.read_sensor(999)
    assert result is False


def test_get_coordinates(sensor_manager):
    """Test getting sensor coordinates."""
    coords = sensor_manager.get_coordinates(1)
    assert coords == (100, 50)

    coords = sensor_manager.get_coordinates(2)
    assert coords == (200, 100)


def test_get_coordinates_nonexistent_sensor(sensor_manager):
    """Test getting coordinates of nonexistent sensor returns None."""
    coords = sensor_manager.get_coordinates(999)
    assert coords is None


def test_move_sensor(sensor_manager):
    """Test moving a sensor to new coordinates."""
    assert sensor_manager.move_sensor(1, (150, 200)) is True
    coords = sensor_manager.get_coordinates(1)
    assert coords == (150, 200)


def test_move_nonexistent_sensor(sensor_manager):
    """Test moving a nonexistent sensor returns False."""
    assert sensor_manager.move_sensor(999, (150, 200)) is False


def test_get_all_sensor_info(sensor_manager):
    """Test getting information of all sensors."""
    info = sensor_manager.get_all_sensor_info()
    assert len(info) == 3
    assert 1 in info
    assert 2 in info
    assert 3 in info

    # Check sensor 1 info
    sensor1_info = info[1]
    assert sensor1_info.sensor_id == 1
    assert sensor1_info.sensor_type == SensorType.WINDOOR_SENSOR
    assert sensor1_info.coordinate_x == 100
    assert sensor1_info.coordinate_y == 50


def test_if_intrusion_detected_no_intrusion(sensor_manager):
    """Test intrusion detection when no intrusion."""
    sensor_manager.arm_all_sensors()
    assert sensor_manager.if_intrusion_detected() is False


def test_if_intrusion_detected_with_intrusion(sensor_manager):
    """Test intrusion detection when intrusion occurs."""
    sensor_manager.arm_all_sensors()
    sensor_manager.sensor_dict[2].intrude()
    assert sensor_manager.if_intrusion_detected() is True


def test_if_intrusion_detected_disarmed_sensor(sensor_manager):
    """Test intrusion detection ignores disarmed sensors."""
    # Only arm sensor 1
    sensor_manager.arm_sensor(1)

    # Intrude on sensor 2 (which is disarmed)
    sensor_manager.sensor_dict[2].intrude()

    # Should not detect intrusion because sensor 2 is disarmed
    assert sensor_manager.if_intrusion_detected() is False


def test_add_sensor_not_implemented(sensor_manager):
    """Test that add_sensor raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        sensor_manager.add_sensor(4, None)


def test_remove_sensor_not_implemented(sensor_manager):
    """Test that remove_sensor raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        sensor_manager.remove_sensor(1)


def test_empty_sensor_manager():
    """Test SensorManager with no sensors."""
    manager = SensorManager()
    assert len(manager.sensor_dict) == 0
    assert manager.sensor_ids == []
    assert manager.arm_all_sensors() is True
    assert manager.disarm_all_sensors() is True
    assert manager.if_intrusion_detected() is False
    assert manager.read_sensor(1) is False
    assert manager.get_coordinates(1) is None
    assert manager.arm_sensor(1) is False
    assert manager.disarm_sensor(1) is False
    assert manager.move_sensor(1, (0, 0)) is False
