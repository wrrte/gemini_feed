"""
Integration Test: ConfigurationManager + SensorManager

Tests the interaction between ConfigurationManager and SensorManager.
Verifies SafetyZone/SafeHomeMode changes affect sensor arm/disarm states.

Note: StorageManager is mocked as it's an external boundary (DB access).
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from database.schema.safehome_mode import SafeHomeModeSchema
from database.schema.safety_zone import SafetyZoneSchema
from database.schema.sensor import SensorSchema, SensorType
from database.schema.system_setting import SystemSettingSchema
from device.sensor.motion_detector_sensor import MotionDetectorSensor
from device.sensor.window_door_sensor import WindowDoorSensor
from manager.configuration_manager import ConfigurationManager
from manager.sensor_manager import SensorManager

# ==================== Fixtures ====================


@pytest.fixture
def mock_storage_manager():
    """Create a mock StorageManager (external boundary)."""
    mock = Mock()

    # Mock system settings
    mock.get_system_setting.return_value = SystemSettingSchema(
        system_setting_id=1,
        panic_phone_number="911",
        homeowner_phone_number="555-1234",
        system_lock_time=30,
        alarm_delay_time=10,
    )

    # Mock safehome modes
    mock.get_all_safehome_modes.return_value = [
        SafeHomeModeSchema(
            mode_id=1,
            mode_name="Home",
            sensor_ids=[1],  # Only sensor 1 armed in Home mode
            created_at=datetime.now(),
        ),
        SafeHomeModeSchema(
            mode_id=2,
            mode_name="Away",
            sensor_ids=[1, 2, 3],  # All sensors armed in Away mode
            created_at=datetime.now(),
        ),
        SafeHomeModeSchema(
            mode_id=3,
            mode_name="Night",
            sensor_ids=[2, 3],  # Sensors 2, 3 armed in Night mode
            created_at=datetime.now(),
        ),
    ]

    # Mock safety zones
    mock.get_all_safety_zones.return_value = [
        SafetyZoneSchema(
            zone_id=1,
            zone_name="Living Room",
            coordinate_x1=0,
            coordinate_y1=0,
            coordinate_x2=100,
            coordinate_y2=100,
            arm_status=False,
        ),
        SafetyZoneSchema(
            zone_id=2,
            zone_name="Bedroom",
            coordinate_x1=100,
            coordinate_y1=0,
            coordinate_x2=200,
            coordinate_y2=100,
            arm_status=False,
        ),
    ]

    # Mock update methods
    mock.update_safehome_mode.return_value = True
    mock.update_safety_zone.return_value = True
    mock.update_sensor.return_value = True
    mock.get_safety_zone.return_value = SafetyZoneSchema(
        zone_id=1,
        zone_name="Living Room",
        coordinate_x1=0,
        coordinate_y1=0,
        coordinate_x2=100,
        coordinate_y2=100,
        arm_status=True,
    )

    return mock


@pytest.fixture
def sensors():
    """Create real sensor instances."""
    sensor1 = WindowDoorSensor(
        SensorSchema(
            sensor_id=1,
            sensor_type=SensorType.WINDOOR_SENSOR,
            coordinate_x=50,
            coordinate_y=50,
            armed=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    )
    sensor2 = WindowDoorSensor(
        SensorSchema(
            sensor_id=2,
            sensor_type=SensorType.WINDOOR_SENSOR,
            coordinate_x=150,
            coordinate_y=50,
            armed=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    )
    sensor3 = MotionDetectorSensor(
        SensorSchema(
            sensor_id=3,
            sensor_type=SensorType.MOTION_DETECTOR_SENSOR,
            coordinate_x=75,
            coordinate_y=75,
            coordinate_x2=125,
            coordinate_y2=125,
            armed=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    )
    return {1: sensor1, 2: sensor2, 3: sensor3}


@pytest.fixture
def sensor_manager(sensors):
    """Create SensorManager with real sensors."""
    return SensorManager(sensor_dict=sensors)


@pytest.fixture
def config_manager(mock_storage_manager, sensor_manager):
    """Create ConfigurationManager with real SensorManager."""
    return ConfigurationManager(
        storage_manager=mock_storage_manager,
        sensor_manager=sensor_manager,
    )


# ==================== SafeHomeMode Integration Tests ====================


def test_change_to_home_mode_arms_correct_sensors(
    config_manager, sensor_manager
):
    """Test changing to Home mode arms only sensor 1."""
    # Act
    result = config_manager.change_to_safehome_mode("Home")

    # Assert
    assert result is True
    assert sensor_manager.get_sensor(1).is_armed() is True
    assert sensor_manager.get_sensor(2).is_armed() is False
    assert sensor_manager.get_sensor(3).is_armed() is False


def test_change_to_away_mode_arms_all_sensors(config_manager, sensor_manager):
    """Test changing to Away mode arms all sensors."""
    # Act
    result = config_manager.change_to_safehome_mode("Away")

    # Assert
    assert result is True
    assert sensor_manager.get_sensor(1).is_armed() is True
    assert sensor_manager.get_sensor(2).is_armed() is True
    assert sensor_manager.get_sensor(3).is_armed() is True


def test_change_to_night_mode_arms_correct_sensors(
    config_manager, sensor_manager
):
    """Test changing to Night mode arms sensors 2 and 3."""
    # Act
    result = config_manager.change_to_safehome_mode("Night")

    # Assert
    assert result is True
    assert sensor_manager.get_sensor(1).is_armed() is False
    assert sensor_manager.get_sensor(2).is_armed() is True
    assert sensor_manager.get_sensor(3).is_armed() is True


def test_change_mode_disarms_previously_armed_sensors(
    config_manager, sensor_manager
):
    """Test that changing modes properly disarms sensors not in new mode."""
    # Arrange - first set to Away mode (all armed)
    config_manager.change_to_safehome_mode("Away")
    assert sensor_manager.get_sensor(1).is_armed() is True
    assert sensor_manager.get_sensor(2).is_armed() is True
    assert sensor_manager.get_sensor(3).is_armed() is True

    # Act - change to Home mode (only sensor 1)
    result = config_manager.change_to_safehome_mode("Home")

    # Assert
    assert result is True
    assert sensor_manager.get_sensor(1).is_armed() is True
    assert sensor_manager.get_sensor(2).is_armed() is False
    assert sensor_manager.get_sensor(3).is_armed() is False


def test_change_to_nonexistent_mode_returns_false(config_manager):
    """Test changing to non-existent mode returns False."""
    # Act
    result = config_manager.change_to_safehome_mode("InvalidMode")

    # Assert
    assert result is False


def test_get_safehome_mode_by_name(config_manager):
    """Test getting SafeHomeMode by name."""
    # Act
    mode = config_manager.get_safehome_mode_by_name("Away")

    # Assert
    assert mode is not None
    assert mode.mode_name == "Away"
    assert set(mode.get_sensor_list()) == {1, 2, 3}


def test_get_safehome_mode_by_id(config_manager):
    """Test getting SafeHomeMode by ID."""
    # Act
    mode = config_manager.get_safehome_mode(1)

    # Assert
    assert mode is not None
    assert mode.mode_name == "Home"


def test_get_all_safehome_modes(config_manager):
    """Test getting all SafeHome modes."""
    # Act
    modes = config_manager.get_all_safehome_modes()

    # Assert
    assert len(modes) == 3
    assert 1 in modes
    assert 2 in modes
    assert 3 in modes


# ==================== SafetyZone Integration Tests ====================


def test_arm_safety_zone_arms_sensors(
    config_manager, sensor_manager, mock_storage_manager
):
    """Test arming a safety zone arms its sensors."""
    # Arrange - add sensors to zone
    zone = config_manager.get_safety_zone(1)
    zone.set_sensor_list([1, 3])

    # Act
    result = config_manager.arm_safety_zone(1)

    # Assert
    assert result is True
    assert sensor_manager.get_sensor(1).is_armed() is True
    assert sensor_manager.get_sensor(3).is_armed() is True
    # Sensor 2 not in zone, should remain disarmed
    assert sensor_manager.get_sensor(2).is_armed() is False


def test_disarm_safety_zone_disarms_sensors(
    config_manager, sensor_manager, mock_storage_manager
):
    """Test disarming a safety zone disarms its sensors."""
    # Arrange - arm zone first
    zone = config_manager.get_safety_zone(1)
    zone.set_sensor_list([1, 3])
    config_manager.arm_safety_zone(1)

    # Act
    result = config_manager.disarm_safety_zone(1)

    # Assert
    assert result is True
    assert sensor_manager.get_sensor(1).is_armed() is False
    assert sensor_manager.get_sensor(3).is_armed() is False


def test_arm_nonexistent_zone_returns_false(config_manager):
    """Test arming non-existent zone returns False."""
    # Act
    result = config_manager.arm_safety_zone(999)

    # Assert
    assert result is False


def test_disarm_nonexistent_zone_returns_false(config_manager):
    """Test disarming non-existent zone returns False."""
    # Act
    result = config_manager.disarm_safety_zone(999)

    # Assert
    assert result is False


def test_get_safety_zone_by_id(config_manager):
    """Test getting SafetyZone by ID."""
    # Act
    zone = config_manager.get_safety_zone(1)

    # Assert
    assert zone is not None
    assert zone.zone_name == "Living Room"


def test_get_all_safety_zones(config_manager):
    """Test getting all safety zones."""
    # Act
    zones = config_manager.get_all_safety_zones()

    # Assert
    assert len(zones) == 2
    assert 1 in zones
    assert 2 in zones


def test_get_safety_zone_invalid_id_type(config_manager):
    """Test getting safety zone with invalid ID type."""
    # Act
    zone = config_manager.get_safety_zone("invalid")

    # Assert
    assert zone is None


# ==================== System Settings Tests ====================


def test_get_system_setting(config_manager):
    """Test getting system settings."""
    # Act
    settings = config_manager.get_system_setting()

    # Assert
    assert settings is not None
    assert settings.panic_phone_number == "911"
    assert settings.homeowner_phone_number == "555-1234"


def test_update_system_setting(config_manager, mock_storage_manager):
    """Test updating system settings."""
    # Arrange
    new_settings = SystemSettingSchema(
        system_setting_id=1,
        panic_phone_number="112",
        homeowner_phone_number="555-9999",
        system_lock_time=60,
        alarm_delay_time=20,
    )

    # Act
    result = config_manager.update_system_setting(new_settings)

    # Assert
    assert result is True
    mock_storage_manager.update_system_setting.assert_called_once_with(
        new_settings
    )


# ==================== Complex Scenario Tests ====================


def test_mode_change_then_zone_arm(config_manager, sensor_manager):
    """Test mode change followed by zone arm."""
    # Arrange - set Home mode (only sensor 1)
    config_manager.change_to_safehome_mode("Home")
    assert sensor_manager.get_sensor(1).is_armed() is True
    assert sensor_manager.get_sensor(2).is_armed() is False

    # Add sensor 2 to zone 2
    zone = config_manager.get_safety_zone(2)
    zone.set_sensor_list([2])

    # Act - arm zone 2
    config_manager.arm_safety_zone(2)

    # Assert - sensor 2 now armed from zone
    assert sensor_manager.get_sensor(2).is_armed() is True


def test_multiple_zones_with_shared_sensor(
    config_manager, sensor_manager, mock_storage_manager
):
    """Test motion detector shared between zones."""
    # Arrange - sensor 3 (motion detector) in both zones
    zone1 = config_manager.get_safety_zone(1)
    zone2 = config_manager.get_safety_zone(2)
    zone1.set_sensor_list([1, 3])  # Zone 1: sensors 1, 3
    zone2.set_sensor_list([2, 3])  # Zone 2: sensors 2, 3

    # Act - arm both zones
    config_manager.arm_safety_zone(1)
    config_manager.arm_safety_zone(2)

    # Assert - all sensors armed
    assert sensor_manager.get_sensor(1).is_armed() is True
    assert sensor_manager.get_sensor(2).is_armed() is True
    assert sensor_manager.get_sensor(3).is_armed() is True

    # Act - disarm zone 1
    # Update mock to return zone2 with armed status for _is_sensor_needed check
    mock_storage_manager.get_safety_zone.return_value = SafetyZoneSchema(
        zone_id=1,
        zone_name="Living Room",
        coordinate_x1=0,
        coordinate_y1=0,
        coordinate_x2=100,
        coordinate_y2=100,
        arm_status=False,
    )
    config_manager.disarm_safety_zone(1)

    # Assert - sensor 3 should stay armed (needed by zone 2)
    assert sensor_manager.get_sensor(1).is_armed() is False
    # Motion detector stays armed because zone 2 still
    #  needs it and has other armed sensors
    assert sensor_manager.get_sensor(3).is_armed() is True
    assert sensor_manager.get_sensor(2).is_armed() is True


def test_update_safehome_mode(config_manager, mock_storage_manager):
    """Test updating a SafeHome mode configuration."""
    # Arrange
    updated_schema = SafeHomeModeSchema(
        mode_id=1,
        mode_name="Home",
        sensor_ids=[1, 2],  # Add sensor 2 to Home mode
        created_at=datetime.now(),
    )

    # Act
    result = config_manager.update_safehome_mode(updated_schema)

    # Assert
    assert result is True
    mock_storage_manager.update_safehome_mode.assert_called_once()


def test_update_nonexistent_safehome_mode(config_manager):
    """Test updating non-existent SafeHome mode."""
    # Arrange
    schema = SafeHomeModeSchema(
        mode_id=999,
        mode_name="Invalid",
        sensor_ids=[],
    )

    # Act
    result = config_manager.update_safehome_mode(schema)

    # Assert
    assert result is False


def test_get_safehome_mode_invalid_id_type(config_manager):
    """Test getting SafeHome mode with invalid ID type."""
    # Act
    mode = config_manager.get_safehome_mode("invalid")

    # Assert
    assert mode is None
