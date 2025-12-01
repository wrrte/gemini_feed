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


def test_arm_disarm_single(sensor_manager, mock_sensor):
    assert sensor_manager.arm_sensor(1) is True
    mock_sensor.arm.assert_called_once()

    assert sensor_manager.disarm_sensor(1) is True
    mock_sensor.disarm.assert_called_once()


def test_arm_disarm_multiple(sensor_manager, mock_sensor):
    sensor_manager.arm_sensors([1])
    mock_sensor.arm.assert_called()

    sensor_manager.disarm_sensors([1])
    mock_sensor.disarm.assert_called()


def test_arm_disarm_all(sensor_manager, mock_sensor):
    sensor_manager.arm_all_sensors()
    mock_sensor.arm.assert_called()

    sensor_manager.disarm_all_sensors()
    mock_sensor.disarm.assert_called()


def test_intrude_release(sensor_manager, mock_sensor):
    sensor_manager.intrude_sensor(1)
    mock_sensor.intrude.assert_called_once()

    sensor_manager.release_sensor(1)
    mock_sensor.release.assert_called_once()


def test_read_sensor(sensor_manager, mock_sensor):
    mock_sensor.read.return_value = True
    assert sensor_manager.read_sensor(1) is True

    mock_sensor.read.return_value = False
    assert sensor_manager.read_sensor(1) is False


def test_move_sensor(sensor_manager, mock_sensor):
    assert sensor_manager.move_sensor(1, (10, 10)) is True
    assert mock_sensor.coordinate_x == 10
    assert mock_sensor.coordinate_y == 10


def test_get_coordinates(sensor_manager, mock_sensor):
    assert sensor_manager.get_coordinates(1) == (0, 0)


def test_get_all_sensor_info(sensor_manager):
    info = sensor_manager.get_all_sensor_info()
    assert 1 in info
    assert info[1].sensor_id == 1
    assert info[1].created_at == datetime(2024, 1, 1, 0, 0, 0)


def test_start_stop_monitoring(sensor_manager):
    with patch("threading.Thread") as mock_thread:
        sensor_manager.start_monitoring()
        assert sensor_manager._monitoring_active is True
        mock_thread.return_value.start.assert_called_once()

        sensor_manager.stop_monitoring()
        assert sensor_manager._monitoring_active is False
        mock_thread.return_value.join.assert_called()


def test_check_all_sensors_trigger(sensor_manager, mock_sensor):
    # Setup handle_intrusion callback
    mock_handler = Mock()
    sensor_manager.handle_intrusion = mock_handler

    # Setup sensor state (Armed AND Intrusion detected)
    mock_sensor.is_armed.return_value = True
    mock_sensor.read.return_value = True

    sensor_manager._check_all_sensors()

    mock_handler.assert_called_with(1, SensorType.MOTION_DETECTOR_SENSOR)


def test_not_implemented_methods(sensor_manager):
    with pytest.raises(NotImplementedError):
        sensor_manager.add_sensor(2, Mock())
    with pytest.raises(NotImplementedError):
        sensor_manager.remove_sensor(1)


def test_invalid_sensor_id_operations(sensor_manager):
    invalid_id = 999

    assert sensor_manager.arm_sensor(invalid_id) is False
    assert sensor_manager.disarm_sensor(invalid_id) is False
    assert sensor_manager.intrude_sensor(invalid_id) is False
    assert sensor_manager.release_sensor(invalid_id) is False
    assert sensor_manager.read_sensor(invalid_id) is False
    assert sensor_manager.get_coordinates(invalid_id) is None
    assert sensor_manager.move_sensor(invalid_id, (5, 5)) is False

    assert sensor_manager.arm_sensors([invalid_id]) is True
    assert sensor_manager.disarm_sensors([invalid_id]) is True


def test_if_intrusion_detected(sensor_manager, mock_sensor):
    mock_sensor.read.return_value = False
    assert sensor_manager.if_intrusion_detected() is False

    mock_sensor.read.return_value = True
    assert sensor_manager.if_intrusion_detected() is True


def test_start_monitoring_already_active(sensor_manager):
    sensor_manager._monitoring_active = True
    with patch("threading.Thread") as mock_thread:
        sensor_manager.start_monitoring()
        mock_thread.assert_not_called()


def test_stop_monitoring_not_active(sensor_manager):
    sensor_manager._monitoring_active = False
    sensor_manager.stop_monitoring()
    if sensor_manager._monitor_thread:
        sensor_manager._monitor_thread.join.assert_not_called()


def test_monitor_loop_exception(sensor_manager):
    sensor_manager._monitoring_active = True

    mock_log_manager = Mock()
    sensor_manager.log_manager = mock_log_manager

    with patch.object(sensor_manager,
                      '_check_all_sensors',
                      side_effect=Exception("Test Loop Error")), \
            patch("time.sleep",
                  side_effect=lambda x: setattr(
                      sensor_manager,
                      '_monitoring_active', False)):

        sensor_manager._monitor_sensors_loop()

    mock_log_manager.error.assert_called()


def test_check_all_sensors_no_trigger(sensor_manager, mock_sensor):
    sensor_manager.handle_intrusion = Mock()

    mock_sensor.is_armed.return_value = False
    mock_sensor.read.return_value = True
    sensor_manager._check_all_sensors()
    sensor_manager.handle_intrusion.assert_not_called()

    mock_sensor.is_armed.return_value = True
    mock_sensor.read.return_value = False
    sensor_manager._check_all_sensors()
    sensor_manager.handle_intrusion.assert_not_called()
