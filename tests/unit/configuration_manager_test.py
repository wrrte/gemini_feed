import pytest
from unittest.mock import Mock, patch
from manager.configuration_manager import ConfigurationManager
from manager.storage_manager import StorageManager
from manager.sensor_manager import SensorManager
from database.schema.safehome_mode import SafeHomeModeSchema
from database.schema.safety_zone import SafetyZoneSchema

@pytest.fixture
def mock_storage_manager():
    return Mock(spec=StorageManager)

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

# ... (Previous simple tests omitted for brevity, focusing on parametrized ones) ...

@pytest.mark.parametrize("zone_id, found", [(1, True), (999, False)])
def test_get_safety_zone(config_manager, zone_id, found):
    mock_zone = Mock()
    config_manager.safety_zones[1] = mock_zone
    
    result = config_manager.get_safety_zone(zone_id)
    if found:
        assert result == mock_zone
    else:
        assert result is None

@pytest.mark.parametrize("new_coords, expected_overlap", [
    ((5, 5, 15, 15), True),   # Overlap
    ((20, 20, 30, 30), False), # No overlap
    ((0, 0, 10, 10), False),   # Exact match ID (should be skipped if ID matches, but here ID differs)
    ((-5, -5, -1, -1), False)  # Left/Above
])
def test_check_zone_is_overlap(config_manager, new_coords, expected_overlap):
    # Existing zone (0,0) to (10,10)
    existing_zone = Mock()
    existing_zone.zone_id = 1
    existing_zone.get_coordinates.return_value = (0, 0, 10, 10)
    config_manager.safety_zones = {1: existing_zone}
    
    # New Zone
    new_zone = Mock()
    new_zone.zone_id = 2
    new_zone.get_coordinates.return_value = new_coords
    
    assert config_manager._check_zone_is_overlap(new_zone) is expected_overlap

# Note: The logic for ID matching in _check_zone_is_overlap skips the check if IDs match.
def test_check_zone_overlap_same_id(config_manager):
    existing_zone = Mock()
    existing_zone.zone_id = 1
    existing_zone.get_coordinates.return_value = (0, 0, 10, 10)
    config_manager.safety_zones = {1: existing_zone}
    
    new_zone = Mock()
    new_zone.zone_id = 1 # Same ID
    new_zone.get_coordinates.return_value = (5, 5, 15, 15) # Physically overlaps
    
    # Should return False because it skips self-check
    assert config_manager._check_zone_is_overlap(new_zone) is False