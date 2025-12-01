import pytest
from unittest.mock import Mock, patch
from manager.sensor_manager import SensorManager
from device.sensor.interface_sensor import InterfaceSensor
from database.schema.sensor import SensorType

@pytest.fixture
def mock_sensor():
    sensor = Mock(spec=InterfaceSensor)
    sensor.sensor_id = 1
    sensor.coordinate_x = 0
    sensor.coordinate_y = 0
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

def test_move_sensor(sensor_manager, mock_sensor):
    assert sensor_manager.move_sensor(1, (10, 10)) is True
    assert mock_sensor.coordinate_x == 10
    assert mock_sensor.coordinate_y == 10

def test_get_all_sensor_info(sensor_manager):
    info = sensor_manager.get_all_sensor_info()
    assert 1 in info
    assert info[1].sensor_id == 1

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
    
    # Setup sensor state
    mock_sensor.is_armed.return_value = True
    mock_sensor.read.return_value = True
    
    sensor_manager._check_all_sensors()
    
    mock_handler.assert_called_with(1, SensorType.MOTION_DETECTOR_SENSOR)