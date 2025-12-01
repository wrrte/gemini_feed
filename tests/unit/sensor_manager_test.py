from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from database.schema.sensor import SensorType
from device.sensor.interface_sensor import InterfaceSensor
from manager.sensor_manager import SensorManager


@pytest.fixture
def mock_sensor():
    sensor = Mock(spec=InterfaceSensor)
    sensor.sensor_id = 1
    sensor.coordinate_x = 0
    sensor.coordinate_y = 0
    sensor.created_at = datetime(2024, 1, 1, 0, 0, 0)
    sensor.updated_at = datetime(2024, 1, 1, 0, 0, 0)
    sensor.get_type.return_value = SensorType.MOTION_DETECTOR_SENSOR
    return sensor


@pytest.fixture
def sensor_manager(mock_sensor):
    return SensorManager(sensor_dict={1: mock_sensor})


def test_get_sensor(sensor_manager, mock_sensor):
    assert sensor_manager.get_sensor(1) == mock_sensor


def test_arm_disarm_basic(sensor_manager, mock_sensor):
    assert sensor_manager.arm_sensor(1) is True
    assert sensor_manager.disarm_sensor(1) is True
    sensor_manager.arm_sensors([1])
    sensor_manager.disarm_sensors([1])
    sensor_manager.arm_all_sensors()
    sensor_manager.disarm_all_sensors()
    mock_sensor.arm.assert_called()


def test_intrude_release(sensor_manager, mock_sensor):
    assert sensor_manager.intrude_sensor(1) is True
    assert sensor_manager.release_sensor(1) is True


def test_read_sensor(sensor_manager, mock_sensor):
    mock_sensor.read.return_value = True
    assert sensor_manager.read_sensor(1) is True


def test_move_sensor(sensor_manager, mock_sensor):
    assert sensor_manager.move_sensor(1, (10, 10)) is True
    assert mock_sensor.coordinate_x == 10


def test_get_coordinates(sensor_manager):
    assert sensor_manager.get_coordinates(1) == (0, 0)


def test_get_all_sensor_info(sensor_manager):
    info = sensor_manager.get_all_sensor_info()
    assert info[1].sensor_id == 1


def test_start_stop_monitoring(sensor_manager):
    with patch("threading.Thread") as mock_thread:
        sensor_manager.start_monitoring()
        mock_thread.return_value.start.assert_called()
        # Already active
        sensor_manager.start_monitoring()

        sensor_manager.stop_monitoring()
        mock_thread.return_value.join.assert_called()
        # Not active
        sensor_manager.stop_monitoring()


def test_check_all_sensors_logic(sensor_manager, mock_sensor):
    sensor_manager.handle_intrusion = Mock()

    # Trigger intrusion
    mock_sensor.is_armed.return_value = True
    mock_sensor.read.return_value = True
    sensor_manager._check_all_sensors()
    sensor_manager.handle_intrusion.assert_called()

    # No intrusion
    mock_sensor.read.return_value = False
    sensor_manager.handle_intrusion.reset_mock()
    sensor_manager._check_all_sensors()
    sensor_manager.handle_intrusion.assert_not_called()


def test_not_implemented(sensor_manager):
    with pytest.raises(NotImplementedError):
        sensor_manager.add_sensor(2, Mock())
    with pytest.raises(NotImplementedError):
        sensor_manager.remove_sensor(1)


def test_invalid_sensor_id_ops(sensor_manager):
    id = 999
    assert sensor_manager.arm_sensor(id) is False
    assert sensor_manager.disarm_sensor(id) is False
    assert sensor_manager.intrude_sensor(id) is False
    assert sensor_manager.release_sensor(id) is False
    assert sensor_manager.read_sensor(id) is False
    assert sensor_manager.get_coordinates(id) is None
    assert sensor_manager.move_sensor(id, (0, 0)) is False
    assert sensor_manager.arm_sensors([id]) is True
    assert sensor_manager.disarm_sensors([id]) is True


def test_if_intrusion_detected(sensor_manager, mock_sensor):
    mock_sensor.read.return_value = False
    assert sensor_manager.if_intrusion_detected() is False
    mock_sensor.read.return_value = True
    assert sensor_manager.if_intrusion_detected() is True


def test_monitor_loop_exception(sensor_manager):
    sensor_manager._monitoring_active = True
    sensor_manager.log_manager = Mock()

    # raise exception then stop loop
    def side_effect():
        sensor_manager._monitoring_active = False
        raise Exception("Loop Error")

    with patch.object(sensor_manager, '_check_all_sensors',
                      side_effect=side_effect):
        sensor_manager._monitor_sensors_loop()

    sensor_manager.log_manager.error.assert_called()