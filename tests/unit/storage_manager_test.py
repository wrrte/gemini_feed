import sqlite3
from unittest.mock import Mock, mock_open, patch

import pytest

from manager.storage_manager import StorageManager

# ==========================================
# Test Fixtures & Setup
# ==========================================


@pytest.fixture
def mock_db_schema():
    """Returns SQL schema for in-memory database setup."""
    return """
    CREATE TABLE users (
        user_id TEXT PRIMARY KEY, role TEXT, panel_id TEXT,
        panel_password TEXT, web_id TEXT, web_password TEXT
    );
    CREATE TABLE logs (
        level TEXT, filename TEXT, function_name TEXT,
        line_number INTEGER, message TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE system_settings (
        system_setting_id INTEGER PRIMARY KEY,
        panic_phone_number TEXT, homeowner_phone_number TEXT,
        system_lock_time INTEGER, alarm_delay_time INTEGER,
        updated_at DATETIME
    );
    CREATE TABLE safehome_modes (
        mode_id INTEGER PRIMARY KEY AUTOINCREMENT,
        mode_name TEXT, created_at DATETIME, updated_at DATETIME
    );
    CREATE TABLE safehome_mode_sensors (
        mode_id INTEGER, sensor_id INTEGER,
        PRIMARY KEY (mode_id, sensor_id)
    );
    CREATE TABLE safety_zones (
        zone_id INTEGER PRIMARY KEY AUTOINCREMENT,
        zone_name TEXT, coordinate_x1 INTEGER, coordinate_y1 INTEGER,
        coordinate_x2 INTEGER, coordinate_y2 INTEGER, arm_status INTEGER,
        created_at DATETIME, updated_at DATETIME
    );
    CREATE TABLE sensors (
        sensor_id INTEGER PRIMARY KEY, sensor_type INTEGER,
        coordinate_x INTEGER, coordinate_y INTEGER,
        coordinate_x2 INTEGER, coordinate_y2 INTEGER, armed INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE cameras (
        camera_id INTEGER PRIMARY KEY, coordinate_x INTEGER,
        coordinate_y INTEGER, pan INTEGER, zoom_setting INTEGER,
        has_password INTEGER, password TEXT, enabled INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """


@pytest.fixture
def manager(mock_db_schema):
    """
    Fixture for StorageManager with in-memory SQLite database.
    Prevents __del__ from resetting singleton state during test execution.
    """
    StorageManager._instance = None

    # Patch __del__ to prevent GC of old instances from wiping the new
    # singleton
    with patch.object(StorageManager, "__del__", lambda self: None):
        with patch.object(StorageManager, "_create_tables"):
            mgr = StorageManager(db_path=":memory:", reset_database=False)

            # Ensure instantiation succeeded
            if mgr is None:
                raise RuntimeError("StorageManager failed to instantiate.")

            if mgr.connection:
                mgr.connection.executescript(mock_db_schema)
                mgr.connection.commit()

            yield mgr

            # Cleanup explicitly
            mgr.clean_up()
            StorageManager._instance = None


# ==========================================
# Initialization Tests
# ==========================================


def test_singleton_pattern(manager):
    m2 = StorageManager(db_path=":memory:")
    assert manager is m2


def test_initialize_with_custom_path():
    StorageManager._instance = None
    custom_path = "/tmp/test_db/safehome.db"

    with (
        patch("os.path.exists", return_value=False),
        patch("os.makedirs") as mock_makedirs,
        patch.object(StorageManager, "_connect"),
        patch.object(StorageManager, "_create_tables"),
    ):
        StorageManager(db_path=custom_path)
        mock_makedirs.assert_called_once()

    StorageManager._instance = None


def test_init_default_path_create_dir():
    StorageManager._instance = None
    # Mocking abspath to return a fake path to test mkdir logic
    with (
        patch("os.path.abspath", return_value="/a/b/c/file.py"),
        patch("os.path.exists", return_value=False),
        patch("os.makedirs") as mock_makedirs,
        patch("sqlite3.connect"),
        patch.object(StorageManager, "_create_tables"),
    ):
        StorageManager()  # db_path is None
        # /a/b/c -> /a/b -> /a/b/database
        mock_makedirs.assert_called()

    StorageManager._instance = None


def test_connect_failure():
    StorageManager._instance = None
    with patch("sqlite3.connect", side_effect=sqlite3.Error("Fail")):
        mgr = StorageManager(db_path=":memory:")
        assert mgr.connection is None
    StorageManager._instance = None


def test_create_tables_file_found():
    StorageManager._instance = None
    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data="CREATE TABLE t(a);")),
        patch("sqlite3.connect") as mock_connect,
    ):
        mock_conn_instance = Mock()
        mock_connect.return_value = mock_conn_instance

        StorageManager(db_path=":memory:")
        assert mock_conn_instance.cursor.called
    StorageManager._instance = None


def test_create_tables_file_not_found(capsys):
    StorageManager._instance = None
    with (
        patch("os.path.exists", return_value=False),
        patch("os.makedirs"),
        patch("sqlite3.connect"),
    ):
        StorageManager(db_path=":memory:")
        captured = capsys.readouterr()
        assert "SQL schema file not found" in captured.out
    StorageManager._instance = None


def test_create_tables_exception(capsys):
    StorageManager._instance = None
    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", side_effect=Exception("Read Error")),
        patch("sqlite3.connect"),
    ):
        StorageManager(db_path=":memory:")
        captured = capsys.readouterr()
        assert "Failed to create tables" in captured.out
    StorageManager._instance = None


def test_drop_tables_success(manager):
    cursor = manager.connection.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    assert len(cursor.fetchall()) > 0

    manager._drop_tables()

    cursor.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    assert len(cursor.fetchall()) == 0


def test_drop_tables_no_connection(manager, capsys):
    if manager.connection:
        manager.connection.close()
    manager.connection = None
    manager._drop_tables()
    captured = capsys.readouterr()
    assert "No database connection available" in captured.out


def test_drop_tables_exception(manager, capsys):
    if manager.connection:
        manager.connection.close()
    # Replace real connection with a Mock to simulate error
    manager.connection = Mock()
    manager.connection.cursor.side_effect = sqlite3.Error("Drop Error")

    manager._drop_tables()

    captured = capsys.readouterr()
    assert "Failed to drop tables" in captured.out


def test_initialize_database_data_success():
    StorageManager._instance = None
    with (
        patch.object(StorageManager, "__del__", lambda self: None),
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data="INSERT INTO u VALUES(1)")),
        patch("sqlite3.connect"),
    ):
        mgr = StorageManager(db_path=":memory:", reset_database=True)
        assert mgr.connection is not None
    StorageManager._instance = None


def test_init_data_no_connection(manager, capsys):
    if manager.connection:
        manager.connection.close()
    manager.connection = None
    manager._initialize_database_data()
    captured = capsys.readouterr()
    assert "No database connection available" in captured.out


def test_init_data_file_not_found(manager, capsys):
    with patch("os.path.exists", return_value=False):
        manager._initialize_database_data()
        captured = capsys.readouterr()
        assert "SQL data file not found" in captured.out


def test_init_data_exception(manager):
    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data="SQL")),
    ):
        if manager.connection:
            manager.connection.close()
        # Replace real connection with Mock
        manager.connection = Mock()
        manager.connection.cursor.side_effect = sqlite3.Error("Fail")

        with pytest.raises(sqlite3.Error):
            manager._initialize_database_data()


# ==========================================
# User CRUD Tests
# ==========================================


def test_insert_user_success(manager):
    result = manager.insert_user(
        "test_user", "ADMIN", "pid", "ppass", "wid", "wpass"
    )
    assert result is True

    user = manager.get_user("test_user")
    assert user is not None
    assert user["role"] == "ADMIN"


def test_insert_user_failure(manager):
    manager.insert_user("u1", "R", "p", "p")
    result = manager.insert_user("u1", "R", "p", "p")
    assert result is False


def test_get_user_not_found(manager):
    assert manager.get_user("nonexistent") is None


def test_update_user_success(manager):
    manager.insert_user("u1", "OLD", "p", "p")
    result = manager.update_user("u1", role="NEW", panel_id="new_pid")
    assert result is True

    user = manager.get_user("u1")
    assert user["role"] == "NEW"
    assert user["panel_id"] == "new_pid"


def test_update_user_no_args(manager):
    manager.insert_user("u1", "OLD", "p", "p")
    result = manager.update_user("u1")
    assert result is False


def test_update_user_invalid_fields(manager):
    manager.insert_user("u1", "OLD", "p", "p")
    result = manager.update_user("u1", invalid_field="xxx")
    assert result is False


def test_update_user_exception(manager):
    manager.insert_user("u1", "R", "p", "p")
    original_conn = manager.connection
    manager.connection = Mock()
    manager.connection.cursor.side_effect = sqlite3.Error("Update Error")
    try:
        assert manager.update_user("u1", role="X") is False
    finally:
        manager.connection = original_conn


def test_delete_user_success(manager):
    manager.insert_user("u1", "R", "p", "p")
    result = manager.delete_user("u1")
    assert result is True
    assert manager.get_user("u1") is None


def test_delete_user_fail_exception(manager):
    original_conn = manager.connection
    manager.connection = Mock()
    manager.connection.cursor.side_effect = sqlite3.Error("Fail")

    try:
        result = manager.delete_user("u1")
        assert result is False
    finally:
        manager.connection = original_conn


# ==========================================
# Log CRUD Tests
# ==========================================


def test_insert_log_success(manager):
    result = manager.insert_log("INFO", "msg", "file.py", "func", 10)
    assert result is True

    logs = manager.get_logs()
    assert len(logs) == 1
    assert logs[0]["message"] == "msg"


def test_get_logs_with_limit_and_level(manager):
    manager.insert_log("INFO", "info_msg")
    manager.insert_log("ERROR", "error_msg")

    logs = manager.get_logs(level="ERROR")
    assert len(logs) == 1
    assert logs[0]["level"] == "ERROR"


def test_delete_logs_before(manager):
    manager.insert_log("INFO", "msg")
    result = manager.delete_logs_before("2099-01-01")
    assert result is True
    assert len(manager.get_logs()) == 0


def test_delete_logs_exception(manager):
    original_conn = manager.connection
    manager.connection = Mock()
    manager.connection.cursor.side_effect = sqlite3.Error("Fail")
    try:
        assert manager.delete_logs_before("2022") is False
    finally:
        manager.connection = original_conn


# ==========================================
# System Settings Tests
# ==========================================


def test_system_settings_crud(manager):
    mock_setting = Mock()
    mock_setting.panic_phone_number = "123"
    mock_setting.homeowner_phone_number = "456"
    mock_setting.system_lock_time = 10
    mock_setting.alarm_delay_time = 5
    mock_setting.system_setting_id = 1

    assert manager.insert_system_setting(mock_setting) is True

    retrieved = manager.get_system_setting(1)
    assert retrieved is not None
    assert retrieved.panic_phone_number == "123"
    # Test not found
    assert manager.get_system_setting(999) is None

    mock_setting.panic_phone_number = "999"
    assert manager.update_system_setting(mock_setting) is True

    retrieved = manager.get_system_setting(1)
    assert retrieved.panic_phone_number == "999"

    assert manager.delete_system_setting(1) is True
    assert manager.get_system_setting(1) is None


def test_delete_system_setting_exception(manager):
    original_conn = manager.connection
    manager.connection = Mock()
    manager.connection.cursor.side_effect = Exception("DB Error")

    try:
        assert manager.delete_system_setting(1) is False
    finally:
        manager.connection = original_conn


# ==========================================
# SafeHome Mode Tests
# ==========================================


def test_safehome_mode_crud(manager):
    mock_mode = Mock()
    mock_mode.mode_name = "Night"
    mock_mode.sensor_ids = [1, 2]

    # Pre-populate sensors
    manager.connection.execute("""
        INSERT INTO sensors (sensor_id, sensor_type, coordinate_x,
        coordinate_y, coordinate_x2, coordinate_y2, armed)
        VALUES (1, 1, 0, 0, 10, 10, 1)
    """)
    manager.connection.execute("""
        INSERT INTO sensors (sensor_id, sensor_type, coordinate_x,
        coordinate_y, coordinate_x2, coordinate_y2, armed)
        VALUES (2, 1, 0, 0, 10, 10, 1)
    """)
    manager.connection.commit()

    assert manager.insert_safehome_mode(mock_mode) is True

    modes = manager.get_all_safehome_modes()
    assert len(modes) == 1
    assert set(modes[0].sensor_ids) == {1, 2}

    sensors = manager.get_safehome_mode_sensors(modes[0].mode_id)
    assert set(sensors) == {1, 2}

    mock_mode.mode_id = modes[0].mode_id
    mock_mode.mode_name = "Night_Updated"
    mock_mode.sensor_ids = [1]  # Reduced sensors
    assert manager.update_safehome_mode(mock_mode) is True

    modes = manager.get_all_safehome_modes()
    assert modes[0].mode_name == "Night_Updated"
    assert modes[0].sensor_ids == [1]


def test_safehome_mode_empty_and_parsing(manager):
    # Test empty modes
    assert manager.get_all_safehome_modes() == []

    # Test mode with NO sensors
    manager.connection.execute(
        "INSERT INTO safehome_modes (mode_name) VALUES ('Empty')"
    )
    manager.connection.commit()

    modes = manager.get_all_safehome_modes()
    assert len(modes) == 1
    assert modes[0].sensor_ids == []

    # Test empty sensor fetch
    assert manager.get_safehome_mode_sensors(999) == []


def test_insert_safehome_mode_failure(manager):
    mock_mode = Mock()
    mock_mode.mode_name = "Fail"
    mock_mode.sensor_ids = []

    original_conn = manager.connection
    manager.connection = Mock()
    manager.connection.cursor.side_effect = Exception("DB Error")

    try:
        assert manager.insert_safehome_mode(mock_mode) is False
    finally:
        manager.connection = original_conn


def test_update_safehome_mode_failure(manager):
    mock_mode = Mock()
    mock_mode.mode_id = 1
    mock_mode.mode_name = "Fail"

    original_conn = manager.connection
    manager.connection = Mock()
    manager.connection.cursor.side_effect = Exception("DB Error")

    try:
        assert manager.update_safehome_mode(mock_mode) is False
    finally:
        manager.connection = original_conn


# ==========================================
# Safety Zone Tests
# ==========================================


def test_safety_zone_crud(manager):
    mock_zone = Mock()
    mock_zone.zone_name = "Kitchen"
    mock_zone.coordinate_x1 = 0
    mock_zone.coordinate_y1 = 0
    mock_zone.coordinate_x2 = 10
    mock_zone.coordinate_y2 = 10
    mock_zone.arm_status = 1

    assert manager.insert_safety_zone(mock_zone) is True

    zone = manager.get_safety_zone_by_name("Kitchen")
    assert zone is not None
    assert zone.zone_name == "Kitchen"

    zone_by_id = manager.get_safety_zone(zone.zone_id)
    assert zone_by_id.zone_id == zone.zone_id

    mock_zone.zone_id = zone.zone_id
    mock_zone.zone_name = "Kitchen_New"
    assert manager.update_safety_zone(mock_zone) is True

    updated = manager.get_safety_zone(zone.zone_id)
    assert updated.zone_name == "Kitchen_New"

    all_zones = manager.get_all_safety_zones()
    assert len(all_zones) == 1

    assert manager.delete_safety_zone(zone.zone_id) is True
    assert manager.get_safety_zone(zone.zone_id) is None


def test_safety_zone_empty_not_found(manager):
    assert manager.get_all_safety_zones() == []
    assert manager.get_safety_zone(999) is None
    assert manager.get_safety_zone_by_name("NoZone") is None


def test_update_safety_zone_failure(manager):
    mock_zone = Mock()
    mock_zone.zone_id = 999
    # Just mock execute_query on the instance to return None (failure signal)
    with patch.object(manager, "execute_query", return_value=None):
        assert manager.update_safety_zone(mock_zone) is False


def test_update_safety_zone_exception(manager):
    mock_zone = Mock()
    with patch.object(
        manager, "execute_query", side_effect=Exception("Error")
    ):
        assert manager.update_safety_zone(mock_zone) is False


# ==========================================
# Sensor & Camera Tests
# ==========================================


def test_sensor_operations(manager):
    # Pre-populate sensor with FULL data
    manager.connection.execute("""
        INSERT INTO sensors (
            sensor_id, sensor_type, coordinate_x, coordinate_y,
            coordinate_x2, coordinate_y2, armed, created_at, updated_at
        ) VALUES (
            1, 1, 10, 10, 20, 20, 1,
            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
    """)
    manager.connection.commit()

    sensors = manager.get_all_sensors()
    assert len(sensors) == 1
    assert sensors[0].sensor_id == 1

    sensor = manager.get_sensor_by_id(1)
    assert sensor is not None
    assert sensor.sensor_id == 1

    mock_sensor = Mock()
    mock_sensor.sensor_id = 1
    mock_sensor.sensor_type = Mock(value=1)
    mock_sensor.coordinate_x = 10
    mock_sensor.coordinate_y = 10
    mock_sensor.coordinate_x2 = 20
    mock_sensor.coordinate_y2 = 20
    mock_sensor.armed = 0

    assert manager.update_sensor(mock_sensor) is True
    updated = manager.get_sensor_by_id(1)
    assert updated.armed == 0


def test_sensor_empty_not_found(manager):
    assert manager.get_all_sensors() == []
    assert manager.get_sensor_by_id(999) is None


def test_camera_operations(manager):
    # Pre-populate
    manager.connection.execute("""
        INSERT INTO cameras (
            camera_id, coordinate_x, coordinate_y, pan, zoom_setting,
            has_password, password, enabled, created_at, updated_at
        ) VALUES (
            1, 0, 0, 0, 1, 0, 'pass', 1,
            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
    """)
    manager.connection.commit()

    cameras = manager.get_all_cameras()
    assert len(cameras) == 1

    mock_cam = Mock()
    mock_cam.camera_id = 1
    mock_cam.coordinate_x = 5
    mock_cam.coordinate_y = 5
    mock_cam.pan = 0
    mock_cam.zoom_setting = 1
    mock_cam.has_password = 0
    mock_cam.password = ""
    mock_cam.enabled = 0

    assert manager.update_camera(mock_cam) is True
    cameras = manager.get_all_cameras()
    assert cameras[0].enabled == 0


def test_camera_empty(manager):
    assert manager.get_all_cameras() == []


# ==========================================
# Utility Tests
# ==========================================


def test_execute_query_no_connection():
    StorageManager._instance = None
    mgr = StorageManager(db_path=":memory:")
    mgr.close()
    assert mgr.connection is None
    assert mgr.execute_query("SELECT 1") is None
    StorageManager._instance = None


def test_execute_query_exception(manager):
    original_conn = manager.connection
    manager.connection = Mock()
    manager.connection.cursor.side_effect = sqlite3.Error("SQL Error")

    try:
        assert manager.execute_query("SELECT 1") is None
    finally:
        manager.connection = original_conn


def test_close_exception(manager, capsys):
    if manager.connection:
        manager.connection.close()

    # Replace real connection with mock to mock .close()
    mock_conn = Mock()
    mock_conn.close.side_effect = sqlite3.Error("Close Error")
    manager.connection = mock_conn

    manager.close()

    # Should catch and print
    captured = capsys.readouterr()
    assert "Failed to close database connection" in captured.out
    # Current implementation does NOT set connection to None on error


def test_cleanup_and_del(manager):
    manager.clean_up()
    assert manager.connection is None
    assert StorageManager._instance is None
