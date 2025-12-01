import pytest
from unittest.mock import Mock, patch
from manager.configuration_manager import ConfigurationManager
from manager.storage_manager import StorageManager
from manager.sensor_manager import SensorManager
from database.schema.safehome_mode import SafeHomeModeSchema
from database.schema.safety_zone import SafetyZoneSchema
from database.schema.system_setting import SystemSettingSchema
from database.schema.sensor import SensorType

@pytest.fixture
def mock_storage_manager():
    # spec 제거하여 유연한 Mock 사용
    return Mock()

@pytest.fixture
def mock_sensor_manager():
    return Mock(spec=SensorManager)

@pytest.fixture
def config_manager(mock_storage_manager, mock_sensor_manager):
    # Setup default mocks for init
    mock_storage_manager.get_system_setting.return_value = Mock(model_dump=lambda: {})
    mock_storage_manager.get_all_safehome_modes.return_value = []
    mock_storage_manager.get_all_safety_zones.return_value = []
    
    with patch("manager.configuration_manager.SystemSettings"), \
         patch("manager.configuration_manager.SafeHomeMode"), \
         patch("manager.configuration_manager.SafetyZone"):
        return ConfigurationManager(storage_manager=mock_storage_manager, sensor_manager=mock_sensor_manager)

def test_init_loads_data(config_manager, mock_storage_manager):
    mock_storage_manager.get_system_setting.assert_called()
    mock_storage_manager.get_all_safehome_modes.assert_called()
    mock_storage_manager.get_all_safety_zones.assert_called()

def test_init_exception(mock_storage_manager, mock_sensor_manager):
    # _load_system_settings에서 예외 발생 시 프로그램이 죽지 않고 로그만 출력하는지 테스트
    mock_storage_manager.get_system_setting.side_effect = Exception("DB Error")
    
    # 예외가 내부적으로 잡혀야 함
    cm = ConfigurationManager(storage_manager=mock_storage_manager, sensor_manager=mock_sensor_manager)
    assert cm.system_settings is None

def test_get_system_setting(config_manager):
    assert config_manager.get_system_setting() == config_manager.system_settings

def test_update_system_setting(config_manager, mock_storage_manager):
    schema = Mock(spec=SystemSettingSchema)
    schema.model_dump.return_value = {}
    mock_storage_manager.update_system_setting.return_value = True
    
    assert config_manager.update_system_setting(schema) is True
    mock_storage_manager.update_system_setting.assert_called_with(schema)

def test_update_system_setting_fail(config_manager, mock_storage_manager):
    schema = Mock(spec=SystemSettingSchema)
    mock_storage_manager.update_system_setting.return_value = False
    assert config_manager.update_system_setting(schema) is False

def test_update_system_setting_exception(config_manager, mock_storage_manager):
    schema = Mock(spec=SystemSettingSchema)
    mock_storage_manager.update_system_setting.side_effect = Exception("error")
    assert config_manager.update_system_setting(schema) is False

def test_get_safehome_mode(config_manager):
    mock_mode = Mock()
    config_manager.safehome_modes[1] = mock_mode
    assert config_manager.get_safehome_mode(1) == mock_mode
    assert config_manager.get_safehome_mode("invalid") is None

def test_get_safehome_mode_by_name(config_manager):
    mock_mode = Mock()
    mock_mode.mode_name = "Night"
    config_manager.safehome_modes[1] = mock_mode
    
    assert config_manager.get_safehome_mode_by_name("Night") == mock_mode
    assert config_manager.get_safehome_mode_by_name("Day") is None

def test_update_safehome_mode(config_manager, mock_storage_manager):
    config_manager.safehome_modes[1] = Mock()
    schema = Mock(spec=SafeHomeModeSchema)
    schema.mode_id = 1
    schema.model_dump.return_value = {}
    mock_storage_manager.update_safehome_mode.return_value = True
    
    assert config_manager.update_safehome_mode(schema) is True
    mock_storage_manager.update_safehome_mode.assert_called_with(schema)

def test_update_safehome_mode_fail(config_manager, mock_storage_manager):
    # Mode not found
    schema = Mock(spec=SafeHomeModeSchema)
    schema.mode_id = 999
    assert config_manager.update_safehome_mode(schema) is False

    # DB Update fail
    config_manager.safehome_modes[1] = Mock()
    schema.mode_id = 1
    mock_storage_manager.update_safehome_mode.return_value = False
    assert config_manager.update_safehome_mode(schema) is False
    
    # Exception
    mock_storage_manager.update_safehome_mode.side_effect = Exception("error")
    assert config_manager.update_safehome_mode(schema) is False

def test_change_to_safehome_mode(config_manager, mock_sensor_manager):
    mock_mode = Mock()
    mock_mode.mode_name = "Night"
    mock_mode.get_sensor_list.return_value = [1]
    config_manager.safehome_modes[1] = mock_mode
    
    mock_sensor_manager.sensor_dict = {1: Mock(), 2: Mock()}
    
    assert config_manager.change_to_safehome_mode("Night") is True
    mock_sensor_manager.arm_sensor.assert_called_with(1)
    mock_sensor_manager.disarm_sensor.assert_called_with(2)

def test_change_to_safehome_mode_not_found(config_manager):
    assert config_manager.change_to_safehome_mode("Invalid") is False

@pytest.mark.parametrize("zone_id, found", [(1, True), (999, False), ("invalid", False)])
def test_get_safety_zone(config_manager, zone_id, found):
    mock_zone = Mock()
    config_manager.safety_zones[1] = mock_zone
    
    result = config_manager.get_safety_zone(zone_id)
    if found:
        assert result == mock_zone
    else:
        assert result is None

def test_update_safety_zone_methods(config_manager, mock_storage_manager):
    # Setup
    config_manager.safety_zones[1] = Mock()
    schema = Mock(spec=SafetyZoneSchema)
    schema.zone_id = 1
    
    # 1. Success
    mock_storage_manager.update_safety_zone.return_value = True
    mock_storage_manager.get_safety_zone.return_value = Mock(model_dump=lambda: {})
    assert config_manager.update_safety_zone(schema) is True
    
    # 2. Invalid ID type
    schema.zone_id = "1"
    assert config_manager.update_safety_zone(schema) is False
    schema.zone_id = 1 # Reset
    
    # 3. Zone Not Found
    schema.zone_id = 999
    assert config_manager.update_safety_zone(schema) is False
    schema.zone_id = 1 # Reset
    
    # 4. DB Update Fail
    mock_storage_manager.update_safety_zone.return_value = False
    assert config_manager.update_safety_zone(schema) is False
    
    # 5. DB Load Updated Zone Fail
    mock_storage_manager.update_safety_zone.return_value = True
    mock_storage_manager.get_safety_zone.return_value = None
    assert config_manager.update_safety_zone(schema) is False
    
    # 6. Exception
    mock_storage_manager.update_safety_zone.side_effect = Exception("error")
    assert config_manager.update_safety_zone(schema) is False

def test_add_safety_zone(config_manager, mock_storage_manager):
    schema = Mock(spec=SafetyZoneSchema)
    schema.zone_name = "New Zone"
    
    # 1. Success
    mock_storage_manager.insert_safety_zone.return_value = True
    mock_storage_manager.get_safety_zone_by_name.return_value = Mock(model_dump=lambda: {})
    assert config_manager.add_safety_zone(schema) is True
    
    # 2. Insert Fail
    mock_storage_manager.insert_safety_zone.return_value = False
    assert config_manager.add_safety_zone(schema) is False
    
    # 3. Load Fail
    mock_storage_manager.insert_safety_zone.return_value = True
    mock_storage_manager.get_safety_zone_by_name.return_value = None
    assert config_manager.add_safety_zone(schema) is False
    
    # 4. Exception
    mock_storage_manager.insert_safety_zone.side_effect = Exception("error")
    assert config_manager.add_safety_zone(schema) is False

def test_delete_safety_zone(config_manager, mock_storage_manager):
    config_manager.safety_zones[1] = Mock()
    
    # 1. Success
    mock_storage_manager.delete_safety_zone.return_value = True
    assert config_manager.delete_safety_zone(1) is True
    assert 1 not in config_manager.safety_zones
    
    # 2. DB Fail
    mock_storage_manager.delete_safety_zone.return_value = False
    assert config_manager.delete_safety_zone(2) is False
    
    # 3. Exception
    mock_storage_manager.delete_safety_zone.side_effect = Exception("error")
    assert config_manager.delete_safety_zone(3) is False

def test_arm_disarm_safety_zone(config_manager, mock_sensor_manager, mock_storage_manager):
    # Setup
    mock_zone = Mock()
    mock_zone.get_sensor_list.return_value = [1]
    mock_zone.to_schema.return_value = Mock()
    config_manager.safety_zones[1] = mock_zone
    
    # Arm Success
    mock_sensor = Mock()
    mock_sensor.is_armed.return_value = True
    mock_sensor_manager.sensor_dict = {1: mock_sensor}
    assert config_manager.arm_safety_zone(1) is True
    
    # Arm Fail (Zone not found)
    assert config_manager.arm_safety_zone(999) is False
    
    # Disarm Success
    # Mocking non-motion sensor for simple disarm path
    mock_sensor.get_type.return_value = SensorType.WINDOW_DOOR_SENSOR
    mock_sensor_manager.get_sensor.return_value = mock_sensor
    assert config_manager.disarm_safety_zone(1) is True
    
    # Disarm Fail (Zone not found)
    assert config_manager.disarm_safety_zone(999) is False

def test_disarm_sensor_in_zone_complex(config_manager, mock_sensor_manager):
    # Test sensor dependency logic (needed by other zones)
    
    # Sensor 1: Motion Detector (Armed)
    sensor1 = Mock()
    sensor1.get_type.return_value = SensorType.MOTION_DETECTOR_SENSOR
    sensor1.is_armed.return_value = True
    
    # Zone 1 (To Disarm): Has Sensor 1
    zone1 = Mock()
    zone1.zone_id = 1
    zone1.get_sensor_list.return_value = [1]
    config_manager.safety_zones[1] = zone1
    
    # Zone 2 (Armed): Has Sensor 1 AND Sensor 2 (Active) -> Sensor 1 is needed
    zone2 = Mock()
    zone2.zone_id = 2
    zone2.is_armed.return_value = True
    zone2.get_sensor_list.return_value = [1, 2]
    config_manager.safety_zones[2] = zone2
    
    # Sensor 2 (Active in Zone 2)
    sensor2 = Mock()
    sensor2.is_armed.return_value = True
    
    mock_sensor_manager.get_sensor.side_effect = lambda id: {1: sensor1, 2: sensor2}.get(id)
    mock_sensor_manager.sensor_dict = {1: sensor1, 2: sensor2}
    
    # Action: Disarm Zone 1
    config_manager._disarm_sensor_in_zone(1, 1)
    
    # Result: Sensor 1 should NOT be disarmed because Zone 2 needs it
    mock_sensor_manager.disarm_sensor.assert_not_called()
    
    # Case: Sensor not found
    mock_sensor_manager.get_sensor.return_value = None
    config_manager._disarm_sensor_in_zone(999, 1) # Should just return

@pytest.mark.parametrize("new_coords, new_id, expected_overlap", [
    # 1. Overlap (Normal)
    ((5, 5, 15, 15), 2, True),
    
    # 2. Same ID (Skip check -> False)
    ((0, 0, 10, 10), 1, False),
    
    # 3. No Overlap - Left (Zone 1 left of Zone 2? No, New Zone left of Existing)
    # Existing: (0,0,10,10). New: (-20, 0, -10, 10)
    # (-10 <= 0) True
    ((-20, 0, -10, 10), 2, False),
    
    # 4. No Overlap - Right
    # New: (20, 0, 30, 10). (20 >= 10) True
    ((20, 0, 30, 10), 2, False),
    
    # 5. No Overlap - Above
    # New: (0, -20, 10, -10). (-10 <= 0) True
    ((0, -20, 10, -10), 2, False),
    
    # 6. No Overlap - Below
    # New: (0, 20, 10, 30). (20 >= 10) True
    ((0, 20, 10, 30), 2, False)
])
def test_check_zone_is_overlap(config_manager, new_coords, new_id, expected_overlap):
    # Existing zone (0,0) to (10,10)
    existing_zone = Mock()
    existing_zone.zone_id = 1
    existing_zone.get_coordinates.return_value = (0, 0, 10, 10)
    config_manager.safety_zones = {1: existing_zone}
    
    # New Zone
    new_zone = Mock()
    new_zone.zone_id = new_id
    new_zone.get_coordinates.return_value = new_coords
    
    assert config_manager._check_zone_is_overlap(new_zone) is expected_overlap

def test_check_zone_is_overlap_no_id(config_manager):
    # Test case where new_zone.zone_id is None (e.g., creating new zone)
    existing_zone = Mock()
    existing_zone.zone_id = 1
    existing_zone.get_coordinates.return_value = (0, 0, 10, 10)
    config_manager.safety_zones = {1: existing_zone}
    
    new_zone = Mock()
    new_zone.zone_id = None
    new_zone.get_coordinates.return_value = (5, 5, 15, 15) # Overlap
    
    assert config_manager._check_zone_is_overlap(new_zone) is True

def test_placeholders(config_manager):
    # Coverage for empty methods
    config_manager.clean_up_configuration_manager()
    config_manager.save_configurations()