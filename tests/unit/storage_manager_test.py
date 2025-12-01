import pytest
import sqlite3
import os
from unittest.mock import Mock, patch, mock_open
from manager.storage_manager import StorageManager
# Removed incorrect import: from database.schema.user import UserSchema
from database.schema.system_setting import SystemSettingSchema
from database.schema.safehome_mode import SafeHomeModeSchema
from database.schema.safety_zone import SafetyZoneSchema
from database.schema.sensor import SensorSchema, SensorType
from database.schema.camera import CameraSchema

# Mock SQL Schema to create tables in memory
MOCK_SQL_SCHEMA = """
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    role TEXT,
    panel_id TEXT,
    panel_password TEXT,
    web_id TEXT,
    web_password TEXT,
    updated_at TIMESTAMP
);
CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT,
    filename TEXT,
    function_name TEXT,
    line_number INTEGER,
    message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE system_settings (
    system_setting_id INTEGER PRIMARY KEY,
    panic_phone_number TEXT,
    homeowner_phone_number TEXT,
    system_lock_time INTEGER,
    alarm_delay_time INTEGER,
    updated_at TIMESTAMP
);
CREATE TABLE safehome_modes (
    mode_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mode_name TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
CREATE TABLE safehome_mode_sensors (
    mode_id INTEGER,
    sensor_id INTEGER
);
CREATE TABLE safety_zones (
    zone_id INTEGER PRIMARY KEY AUTOINCREMENT,
    zone_name TEXT,
    coordinate_x1 INTEGER,
    coordinate_y1 INTEGER,
    coordinate_x2 INTEGER,
    coordinate_y2 INTEGER,
    arm_status TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
CREATE TABLE sensors (
    sensor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_type TEXT,
    coordinate_x INTEGER,
    coordinate_y INTEGER,
    coordinate_x2 INTEGER,
    coordinate_y2 INTEGER,
    armed BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
CREATE TABLE cameras (
    camera_id INTEGER PRIMARY KEY AUTOINCREMENT,
    coordinate_x INTEGER,
    coordinate_y INTEGER,
    pan INTEGER,
    zoom_setting INTEGER,
    has_password BOOLEAN,
    password TEXT,
    enabled BOOLEAN,
    updated_at TIMESTAMP
);
"""

@pytest.fixture
def storage_manager():
    # Reset singleton
    StorageManager._instance = None
    
    # Mock file operations to return mock schema and allow "in-memory" setup
    with patch("builtins.open", mock_open(read_data=MOCK_SQL_SCHEMA)), \
         patch("os.path.exists", return_value=True), \
         patch("os.makedirs"):
        
        # Initialize with memory database
        sm = StorageManager(db_path=":memory:", reset_database=True)
        yield sm
        
        sm.close()
        StorageManager._instance = None

def test_user_crud(storage_manager):
    # Insert
    assert storage_manager.insert_user("u1", "admin", "1111", "pass", "web", "pass") is True
    
    # Get
    user = storage_manager.get_user("u1")
    assert user is not None
    assert user["user_id"] == "u1"
    
    # Update
    assert storage_manager.update_user("u1", role="guest") is True
    user = storage_manager.get_user("u1")
    assert user["role"] == "guest"
    
    # Delete
    assert storage_manager.delete_user("u1") is True
    assert storage_manager.get_user("u1") is None

def test_log_crud(storage_manager):
    assert storage_manager.insert_log("INFO", "test message") is True
    logs = storage_manager.get_logs()
    assert len(logs) == 1
    assert logs[0]["message"] == "test message"
    
    # Test delete (mocking timestamp logic difficult with sqlite defaults, verifying call)
    assert storage_manager.delete_logs_before("2099-01-01") is True
    assert len(storage_manager.get_logs()) == 0

def test_system_setting_crud(storage_manager):
    schema = SystemSettingSchema(
        system_setting_id=1,
        panic_phone_number="911",
        homeowner_phone_number="123",
        system_lock_time=10,
        alarm_delay_time=5
    )
    
    assert storage_manager.insert_system_setting(schema) is True
    
    stored = storage_manager.get_system_setting(1)
    assert stored.panic_phone_number == "911"
    
    schema.panic_phone_number = "999"
    assert storage_manager.update_system_setting(schema) is True
    assert storage_manager.get_system_setting(1).panic_phone_number == "999"

def test_safehome_mode_crud(storage_manager):
    schema = SafeHomeModeSchema(mode_name="Night", sensor_ids=[1, 2])
    
    assert storage_manager.insert_safehome_mode(schema) is True
    
    modes = storage_manager.get_all_safehome_modes()
    assert len(modes) == 1
    assert modes[0].mode_name == "Night"
    assert set(modes[0].sensor_ids) == {1, 2}
    
    # Update
    modes[0].mode_name = "Day"
    modes[0].sensor_ids = [3]
    assert storage_manager.update_safehome_mode(modes[0]) is True
    
    updated = storage_manager.get_all_safehome_modes()[0]
    assert updated.mode_name == "Day"
    assert updated.sensor_ids == [3]

def test_safety_zone_crud(storage_manager):
    schema = SafetyZoneSchema(
        zone_id=1, zone_name="Zone1", 
        coordinate_x1=0, coordinate_y1=0, 
        coordinate_x2=10, coordinate_y2=10
    )
    
    assert storage_manager.insert_safety_zone(schema) is True
    
    zone = storage_manager.get_safety_zone_by_name("Zone1")
    assert zone is not None
    
    zone.zone_name = "UpdatedZone"
    assert storage_manager.update_safety_zone(zone) is True
    
    assert storage_manager.delete_safety_zone(zone.zone_id) is True

def test_sensor_and_camera_ops(storage_manager):
    # These read from pre-populated tables usually, or inserted via SQL
    # Testing read empty
    assert storage_manager.get_all_sensors() == []
    assert storage_manager.get_all_cameras() == []
    
    # Manually insert for test
    storage_manager.execute_query("INSERT INTO sensors (sensor_type) VALUES (?)", ("MOTION",))
    assert len(storage_manager.get_all_sensors()) == 1