from unittest.mock import Mock

import pytest

from database.schema.safehome_mode import SafeHomeModeSchema
from database.schema.safety_zone import SafetyZoneSchema
from database.schema.sensor import SensorType
from database.schema.system_setting import SystemSettingSchema
from manager.configuration_manager import ConfigurationManager
from manager.sensor_manager import SensorManager


@pytest.fixture
def mock_storage_manager():
    return Mock()


@pytest.fixture
def mock_sensor_manager():
    return Mock(spec=SensorManager)


@pytest.fixture
def config_manager(mock_storage_manager, mock_sensor_manager):
    # Setup default mocks for init
    mock_settings = Mock()
    mock_settings.model_dump.return_value = {
        "system_setting_id": 1,
        "panic_phone_number": "111",
        "homeowner_phone_number": "222",
        "system_lock_time": 1,
        "alarm_delay_time": 1
    }
    mock_storage_manager.get_system_setting.return_value = mock_settings
    mock_storage_manager.get_all_safehome_modes.return_value = []
    mock_storage_manager.get_all_safety_zones.return_value = []

    return ConfigurationManager(
        storage_manager=mock_storage_manager,
        sensor_manager=mock_sensor_manager)


def test_init_loads_data(mock_storage_manager, mock_sensor_manager):
    # Setup data to ensure loop bodies in _load methods are executed
    mock_mode_schema = Mock()
    mock_mode_schema.model_dump.return_value = {
        "mode_id": 1, "mode_name": "TestMode", "sensor_ids": []}
    mock_storage_manager.get_all_safehome_modes.return_value = [
        mock_mode_schema]

    mock_zone_schema = Mock()
    mock_zone_schema.zone_id = 1
    # Mock attributes accessed directly
    mock_zone_schema.zone_name = "TestZone"
    mock_zone_schema.coordinate_x1 = 0
    mock_zone_schema.coordinate_y1 = 0
    mock_zone_schema.coordinate_x2 = 10
    mock_zone_schema.coordinate_y2 = 10
    mock_zone_schema.arm_status = False
    mock_storage_manager.get_all_safety_zones.return_value = [mock_zone_schema]

    # Setup settings to avoid error log in this test
    mock_settings = Mock()
    mock_settings.model_dump.return_value = {
        "system_setting_id": 1, "panic_phone_number": "1",
        "homeowner_phone_number": "2",
        "system_lock_time": 1, "alarm_delay_time": 1
    }
    mock_storage_manager.get_system_setting.return_value = mock_settings

    cm = ConfigurationManager(
        storage_manager=mock_storage_manager,
        sensor_manager=mock_sensor_manager)

    # Check if loaded into dicts
    assert 1 in cm.safehome_modes
    assert cm.safehome_modes[1].mode_name == "TestMode"
    assert 1 in cm.safety_zones
    assert cm.safety_zones[1].zone_name == "TestZone"


def test_init_exception(mock_storage_manager, mock_sensor_manager):
    mock_storage_manager.get_system_setting.side_effect = Exception(
        "DB Error")
    mock_storage_manager.get_all_safehome_modes.return_value = []
    mock_storage_manager.get_all_safety_zones.return_value = []

    cm = ConfigurationManager(
        storage_manager=mock_storage_manager,
        sensor_manager=mock_sensor_manager)
    assert cm.system_settings is None


def test_load_system_settings_not_found(
        mock_storage_manager, mock_sensor_manager):
    mock_storage_manager.get_system_setting.return_value = None
    mock_storage_manager.get_all_safehome_modes.return_value = []
    mock_storage_manager.get_all_safety_zones.return_value = []

    cm = ConfigurationManager(
        storage_manager=mock_storage_manager,
        sensor_manager=mock_sensor_manager)
    assert cm.system_settings is None


def test_get_system_setting(config_manager):
    assert config_manager.get_system_setting(
    ) == config_manager.system_settings


def test_update_system_setting(config_manager, mock_storage_manager):
    schema = Mock(spec=SystemSettingSchema)
    schema.model_dump.return_value = {
        "system_setting_id": 1,
        "panic_phone_number": "000",
        "homeowner_phone_number": "000",
        "system_lock_time": 5,
        "alarm_delay_time": 5
    }
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
    schema.model_dump.return_value = {
        "mode_id": 1,
        "mode_name": "Updated",
        "sensor_ids": [1, 2]
    }
    mock_storage_manager.update_safehome_mode.return_value = True

    assert config_manager.update_safehome_mode(schema) is True
    mock_storage_manager.update_safehome_mode.assert_called_with(schema)


def test_update_safehome_mode_fail(config_manager, mock_storage_manager):
    schema = Mock(spec=SafeHomeModeSchema)
    schema.mode_id = 999
    assert config_manager.update_safehome_mode(schema) is False

    config_manager.safehome_modes[1] = Mock()
    schema.mode_id = 1
    mock_storage_manager.update_safehome_mode.return_value = False
    assert config_manager.update_safehome_mode(schema) is False

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


@pytest.mark.parametrize("zone_id, found",
                         [(1, True), (999, False), ("invalid", False)])
def test_get_safety_zone(config_manager, zone_id, found):
    mock_zone = Mock()
    config_manager.safety_zones[1] = mock_zone

    result = config_manager.get_safety_zone(zone_id)
    if found:
        assert result == mock_zone
    else:
        assert result is None


def test_update_safety_zone_methods(config_manager, mock_storage_manager):
    config_manager.safety_zones[1] = Mock()
    schema = Mock(spec=SafetyZoneSchema)
    schema.zone_id = 1

    updated_zone_mock = Mock()
    updated_zone_mock.model_dump.return_value = {
        "zone_id": 1,
        "zone_name": "Updated",
        "coordinate_x1": 0, "coordinate_y1": 0,
        "coordinate_x2": 10, "coordinate_y2": 10,
        "sensor_id_list": [],
        "arm_status": False
    }

    mock_storage_manager.update_safety_zone.return_value = True
    mock_storage_manager.get_safety_zone.return_value = updated_zone_mock
    assert config_manager.update_safety_zone(schema) is True

    schema.zone_id = "1"
    assert config_manager.update_safety_zone(schema) is False
    schema.zone_id = 1

    schema.zone_id = 999
    assert config_manager.update_safety_zone(schema) is False
    schema.zone_id = 1

    mock_storage_manager.update_safety_zone.return_value = False
    assert config_manager.update_safety_zone(schema) is False

    mock_storage_manager.update_safety_zone.return_value = True
    mock_storage_manager.get_safety_zone.return_value = None
    assert config_manager.update_safety_zone(schema) is False

    mock_storage_manager.update_safety_zone.side_effect = Exception("error")
    assert config_manager.update_safety_zone(schema) is False


def test_add_safety_zone(config_manager, mock_storage_manager):
    schema = Mock(spec=SafetyZoneSchema)
    schema.zone_name = "New Zone"
    schema.zone_id = 2

    new_zone_mock = Mock()
    new_zone_mock.model_dump.return_value = {
        "zone_id": 2,
        "zone_name": "New Zone",
        "coordinate_x1": 0, "coordinate_y1": 0,
        "coordinate_x2": 10, "coordinate_y2": 10,
        "sensor_id_list": [],
        "arm_status": False
    }

    mock_storage_manager.insert_safety_zone.return_value = True
    mock_storage_manager.get_safety_zone_by_name.return_value = new_zone_mock
    assert config_manager.add_safety_zone(schema) is True

    mock_storage_manager.insert_safety_zone.return_value = False
    assert config_manager.add_safety_zone(schema) is False

    mock_storage_manager.insert_safety_zone.return_value = True
    mock_storage_manager.get_safety_zone_by_name.return_value = None
    assert config_manager.add_safety_zone(schema) is False

    mock_storage_manager.insert_safety_zone.side_effect = Exception("error")
    assert config_manager.add_safety_zone(schema) is False


def test_delete_safety_zone(config_manager, mock_storage_manager):
    config_manager.safety_zones[1] = Mock()

    mock_storage_manager.delete_safety_zone.return_value = True
    assert config_manager.delete_safety_zone(1) is True
    assert 1 not in config_manager.safety_zones

    mock_storage_manager.delete_safety_zone.return_value = False
    assert config_manager.delete_safety_zone(2) is False

    mock_storage_manager.delete_safety_zone.side_effect = Exception("error")
    assert config_manager.delete_safety_zone(3) is False


def test_delete_safety_zone_not_in_cache(config_manager, mock_storage_manager):
    # Setup: Delete returns True from DB, but ID not in cache
    mock_storage_manager.delete_safety_zone.return_value = True
    config_manager.safety_zones = {}  # Empty cache

    assert config_manager.delete_safety_zone(1) is True
    # Ensures 'if zone_id in self.safety_zones' evaluates to False without
    # error


def test_arm_disarm_safety_zone(
        config_manager, mock_sensor_manager, mock_storage_manager):
    mock_zone = Mock()
    mock_zone.get_sensor_list.return_value = [1]
    mock_zone.to_schema.return_value = Mock()
    config_manager.safety_zones[1] = mock_zone

    mock_sensor = Mock()
    mock_sensor.is_armed.return_value = True
    mock_sensor_manager.sensor_dict = {1: mock_sensor}
    assert config_manager.arm_safety_zone(1) is True

    assert config_manager.arm_safety_zone(999) is False

    mock_sensor.get_type.return_value = SensorType.WINDOOR_SENSOR
    mock_sensor_manager.get_sensor.return_value = mock_sensor
    assert config_manager.disarm_safety_zone(1) is True

    assert config_manager.disarm_safety_zone(999) is False


def test_disarm_sensor_in_zone_complex(config_manager, mock_sensor_manager):
    sensor1 = Mock()
    sensor1.get_type.return_value = SensorType.MOTION_DETECTOR_SENSOR
    sensor1.is_armed.return_value = True

    zone1 = Mock()
    zone1.zone_id = 1
    zone1.get_sensor_list.return_value = [1]
    config_manager.safety_zones[1] = zone1

    zone2 = Mock()
    zone2.zone_id = 2
    zone2.is_armed.return_value = True
    zone2.get_sensor_list.return_value = [1, 2]
    config_manager.safety_zones[2] = zone2

    sensor2 = Mock()
    sensor2.is_armed.return_value = True

    mock_sensor_manager.get_sensor.side_effect = lambda id: {
        1: sensor1, 2: sensor2}.get(id)
    mock_sensor_manager.sensor_dict = {1: sensor1, 2: sensor2}

    config_manager._disarm_sensor_in_zone(1, 1)
    mock_sensor_manager.disarm_sensor.assert_not_called()

    zone2.is_armed.return_value = False
    config_manager._disarm_sensor_in_zone(1, 1)
    mock_sensor_manager.disarm_sensor.assert_called_with(1)

    mock_sensor_manager.get_sensor.return_value = None
    config_manager._disarm_sensor_in_zone(999, 1)


def test_zone_has_other_armed_sensors(config_manager, mock_sensor_manager):
    zone = Mock()
    zone.get_sensor_list.return_value = [1, 2, 3]  # Added 3 for missing case

    sensor1 = Mock()
    sensor1.is_armed.return_value = True

    sensor2 = Mock()
    sensor2.is_armed.return_value = False

    # Sensor 3 is missing from dict
    mock_sensor_manager.sensor_dict = {1: sensor1, 2: sensor2}

    assert config_manager._zone_has_other_armed_sensors(
        zone, exclude_sensor_id=2) is True
    assert config_manager._zone_has_other_armed_sensors(
        zone, exclude_sensor_id=1) is False
    assert config_manager._zone_has_other_armed_sensors(zone) is True


def test_missing_sensor_manager_ops(mock_storage_manager):
    # Setup mocks to return empty lists for init to avoid TypeError
    mock_storage_manager.get_system_setting.return_value = Mock(
        model_dump=lambda: {})
    mock_storage_manager.get_all_safehome_modes.return_value = []
    mock_storage_manager.get_all_safety_zones.return_value = []

    # Test internal methods that guard against missing sensor_manager
    cm = ConfigurationManager(
        storage_manager=mock_storage_manager,
        sensor_manager=None)

    # Should simply return without error
    cm._update_all_sensors_in_db()
    cm._sync_zone_arm_state_with_sensors()


@pytest.mark.parametrize("new_coords, new_id, expected_overlap", [
    ((5, 5, 15, 15), 2, True),
    ((0, 0, 10, 10), 1, False),
    ((-20, 0, -10, 10), 2, False),
    ((20, 0, 30, 10), 2, False),
    ((0, -20, 10, -10), 2, False),
    ((0, 20, 10, 30), 2, False)
])
def test_check_zone_is_overlap(
        config_manager, new_coords, new_id, expected_overlap):
    existing_zone = Mock()
    existing_zone.zone_id = 1
    existing_zone.get_coordinates.return_value = (0, 0, 10, 10)
    config_manager.safety_zones = {1: existing_zone}

    new_zone = Mock()
    new_zone.zone_id = new_id
    new_zone.get_coordinates.return_value = new_coords

    assert config_manager._check_zone_is_overlap(new_zone) is expected_overlap


def test_check_zone_is_overlap_no_id(config_manager):
    existing_zone = Mock()
    existing_zone.zone_id = 1
    existing_zone.get_coordinates.return_value = (0, 0, 10, 10)
    config_manager.safety_zones = {1: existing_zone}

    new_zone = Mock()
    new_zone.zone_id = None
    new_zone.get_coordinates.return_value = (5, 5, 15, 15)

    assert config_manager._check_zone_is_overlap(new_zone) is True


def test_placeholders(config_manager):
    config_manager.clean_up_configuration_manager()
    config_manager.save_configurations()
