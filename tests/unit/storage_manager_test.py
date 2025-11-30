import os
import shutil

import pytest

from database.schema.system_setting import SystemSettingSchema
from manager.storage_manager import StorageManager

current_dir = os.path.dirname(os.path.abspath(__file__))
db_dir = os.path.abspath(os.path.join(current_dir, "../../database"))


@pytest.fixture(autouse=True)
def reset_singleton():
    """
    Reset the singleton instance of StorageManager before and after each test.
    This prevents interference between tests.
    """
    # Setup: Reset instance
    StorageManager._instance = None

    yield

    # Teardown: Clean up database connection and reset instance
    if StorageManager._instance:
        if hasattr(StorageManager._instance, "connection"):
            if StorageManager._instance.connection:
                StorageManager._instance.connection.close()

    StorageManager._instance = None

    # Delete test database file
    test_db_path = os.path.join(db_dir, "safehome_test.db")
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture
def manager(reset_singleton):
    """Create a fresh StorageManager for each test."""
    return StorageManager(db_file_name="safehome_test.db", reset_database=True)


def test_singleton_behavior():
    """Test if singleton pattern works correctly"""
    manager1 = StorageManager(db_file_name="safehome_test.db")
    manager2 = StorageManager(db_file_name="safehome_test.db")

    assert manager1 is manager2
    assert id(manager1) == id(manager2)


def test_database_file_creation():
    """Test if database file is created in the specified path"""
    manager = StorageManager(db_file_name="safehome_test.db")

    assert os.path.exists(manager.db_path)
    assert os.path.isfile(manager.db_path)
    assert manager.db_path.endswith("safehome_test.db")


def test_tables_creation():
    """Test if all required tables are created"""
    manager = StorageManager(db_file_name="safehome_test.db")

    cursor = manager.connection.cursor()

    # Check users table
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
    )
    assert cursor.fetchone() is not None

    # Check logs table
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='logs'"
    )
    assert cursor.fetchone() is not None

    # Check system_settings table
    cursor.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name='system_settings'"
    )
    assert cursor.fetchone() is not None


def test_user_insert_and_get():
    """Test inserting and retrieving a user"""
    manager = StorageManager(db_file_name="safehome_test.db")

    # Insert user
    result = manager.insert_user(
        user_id="user123",
        role="HOMEOWNER",
        panel_id="panel123",
        panel_password="pass123",
        web_id="web123",
        web_password="webpass123",
    )
    assert result is True

    # Get user by ID
    user = manager.get_user("user123")
    assert user is not None
    assert user["user_id"] == "user123"
    assert user["role"] == "HOMEOWNER"
    assert user["panel_id"] == "panel123"
    assert user["web_id"] == "web123"


def test_user_update():
    """Test updating user information"""
    manager = StorageManager(db_file_name="safehome_test.db")

    # Insert user
    manager.insert_user(
        user_id="user456",
        role="GUEST",
        panel_id="panel456",
        panel_password="1234",
    )

    # Update user
    result = manager.update_user(
        "user456",
        panel_password="5678",
    )
    assert result is True

    # Verify update
    user = manager.get_user("user456")
    assert user["panel_id"] == "panel456"
    assert user["panel_password"] == "5678"


def test_user_delete():
    """Test deleting a user"""
    manager = StorageManager(db_file_name="safehome_test.db")

    # Insert user
    manager.insert_user(
        user_id="user789",
        role="GUEST",
        panel_id="panel789",
        panel_password="1234",
    )

    # Verify user exists
    user = manager.get_user("user789")
    assert user is not None

    # Delete user
    result = manager.delete_user("user789")
    assert result is True

    # Verify user is deleted
    user = manager.get_user("user789")
    assert user is None


def test_user_unique_id_constraint():
    """Test that user_id uniqueness is enforced"""
    manager = StorageManager(db_file_name="safehome_test.db")

    # Insert first user
    result1 = manager.insert_user(
        user_id="user001",
        role="HOMEOWNER",
        panel_id="panel001",
        panel_password="pass001",
        web_id="web001",
        web_password="webpass001",
    )
    assert result1 is True

    # Try to insert second user with same user_id
    result2 = manager.insert_user(
        user_id="user001",  # Same user_id
        role="GUEST",
        panel_id="panel002",
        panel_password="pass002",
        web_id="web002",
        web_password="webpass002",
    )
    assert result2 is False  # Should fail due to unique constraint


def test_log_insert_and_get():
    """Test inserting and retrieving logs"""
    manager = StorageManager(db_file_name="safehome_test.db")

    # Insert logs
    manager.insert_log("INFO", "Test info message", "test.py", "test_func")
    manager.insert_log("ERROR", "Test error message", "error.py", "error_func")
    manager.insert_log("DEBUG", "Test debug message")

    # Get all logs
    logs = manager.get_logs(limit=10)
    assert len(logs) >= 3

    # Verify log content (most recent first due to DESC order)
    assert any(log["message"] == "Test info message" for log in logs)
    assert any(log["message"] == "Test error message" for log in logs)
    assert any(log["message"] == "Test debug message" for log in logs)


def test_log_filter_by_level():
    """Test filtering logs by level"""
    manager = StorageManager(db_file_name="safehome_test.db")

    # Insert logs with different levels
    manager.insert_log("INFO", "Info message 1")
    manager.insert_log("INFO", "Info message 2")
    manager.insert_log("ERROR", "Error message 1")
    manager.insert_log("WARNING", "Warning message 1")

    # Get only INFO logs
    info_logs = manager.get_logs(limit=10, level="INFO")
    assert len(info_logs) == 2
    assert all(log["level"] == "INFO" for log in info_logs)

    # Get only ERROR logs
    error_logs = manager.get_logs(limit=10, level="ERROR")
    assert len(error_logs) == 1
    assert error_logs[0]["level"] == "ERROR"


def test_log_delete_before_timestamp():
    """Test deleting logs before a specific timestamp"""
    manager = StorageManager(db_file_name="safehome_test.db")

    # Insert logs
    manager.insert_log("INFO", "Old log 1")
    manager.insert_log("INFO", "Old log 2")

    # Get current timestamp (after inserting logs)
    import datetime

    future_time = datetime.datetime.now() + datetime.timedelta(seconds=1)
    future_timestamp = future_time.strftime("%Y-%m-%d %H:%M:%S")

    # Delete logs before future timestamp (should delete all)
    result = manager.delete_logs_before(future_timestamp)
    assert result is True

    # Verify logs are deleted
    logs = manager.get_logs(limit=10)
    assert len(logs) == 0


def test_system_setting_insert_and_get(manager):
    """Test inserting and retrieving system settings"""
    # Insert a new system setting
    schema = SystemSettingSchema(
        system_setting_id=2,
        panic_phone_number="112",
        homeowner_phone_number="010-9999-9999",
        system_lock_time=45,
        alarm_delay_time=90,
    )
    result = manager.insert_system_setting(schema)
    assert result is True

    # Get the newly inserted setting
    retrieved = manager.get_system_setting(2)
    assert retrieved is not None
    assert retrieved.panic_phone_number == "112"
    assert retrieved.homeowner_phone_number == "010-9999-9999"
    assert retrieved.system_lock_time == 45
    assert retrieved.alarm_delay_time == 90

    # Get non-existent setting
    non_existent = manager.get_system_setting(999)
    assert non_existent is None


def test_system_setting_update(manager):
    """Test updating system settings"""
    # Insert initial system setting
    schema = SystemSettingSchema(
        system_setting_id=1,
        panic_phone_number="119",
        homeowner_phone_number="010-1234-5678",
        system_lock_time=30,
        alarm_delay_time=60,
    )
    manager.insert_system_setting(schema)

    # Update system setting
    updated_schema = SystemSettingSchema(
        system_setting_id=1,
        panic_phone_number="112",
        homeowner_phone_number="010-9876-5432",
        system_lock_time=45,
        alarm_delay_time=90,
    )
    result = manager.update_system_setting(updated_schema)
    assert result is True

    # Verify update
    retrieved = manager.get_system_setting(1)
    assert retrieved.panic_phone_number == "112"
    assert retrieved.homeowner_phone_number == "010-9876-5432"
    assert retrieved.system_lock_time == 45
    assert retrieved.alarm_delay_time == 90


def test_system_setting_delete(manager):
    """Test deleting system setting"""
    # Insert system setting with ID=2
    schema = SystemSettingSchema(
        system_setting_id=2,
        panic_phone_number="119",
        homeowner_phone_number="010-1234-5678",
        system_lock_time=30,
        alarm_delay_time=60,
    )
    manager.insert_system_setting(schema)
    assert manager.get_system_setting(2) is not None

    # Delete system setting
    result = manager.delete_system_setting(2)
    assert result is True

    # Verify deletion
    deleted = manager.get_system_setting(2)
    assert deleted is None

    # Try deleting non-existent system setting
    result = manager.delete_system_setting(999)
    assert result is False


def test_execute_query_select():
    """Test execute_query with SELECT statement"""
    manager = StorageManager(db_file_name="safehome_test.db")

    # Insert test data
    manager.insert_user(
        user_id="query_test",
        role="GUEST",
        panel_id="panel_query",
        panel_password="1234",
    )

    # Execute raw SELECT query
    result = manager.execute_query(
        "SELECT * FROM users WHERE user_id = ?", ("query_test",)
    )

    assert result is not None
    assert len(result) == 1
    assert result[0]["user_id"] == "query_test"


def test_execute_query_insert(manager):
    """Test execute_query with INSERT statement"""
    # Execute raw INSERT query on users table
    result = manager.execute_query(
        "INSERT INTO users (user_id, role, panel_id) VALUES (?, ?, ?)",
        ("test_user", "GUEST", "test_panel"),
    )

    # For non-SELECT queries, result should be empty list on success
    assert result is not None
    assert result == []

    # Verify insertion
    user = manager.get_user("test_user")
    assert user is not None
    assert user["user_id"] == "test_user"


def test_database_directory_auto_creation():
    """Test if database directory is automatically created"""
    custom_db_dir = os.path.join(db_dir, "test_auto_create")
    custom_db_path = os.path.join(custom_db_dir, "safehome_test.db")

    # Ensure directory doesn't exist
    if os.path.exists(custom_db_dir):
        shutil.rmtree(custom_db_dir)

    # Create manager with custom path
    manager = StorageManager(db_path=custom_db_path)

    # Verify directory was created
    assert os.path.exists(custom_db_dir)
    assert os.path.exists(custom_db_path)

    # Cleanup
    manager.close()
    if os.path.exists(custom_db_dir):
        shutil.rmtree(custom_db_dir)


def test_connection_persistence():
    """Test that database connection persists across operations"""
    manager = StorageManager(db_file_name="safehome_test.db")

    # Perform multiple operations
    manager.insert_user(
        user_id="user1",
        role="HOMEOWNER",
        panel_id="panel1",
        panel_password="1234",
        web_id="web1",
        web_password="12345678",
    )
    # Insert system setting
    schema = SystemSettingSchema(
        system_setting_id=1,
        panic_phone_number="119",
    )
    manager.insert_system_setting(schema)
    manager.insert_log("INFO", "Log message")

    # All operations should succeed with same connection
    assert manager.get_user("user1") is not None
    assert manager.get_system_setting(1) is not None
    assert len(manager.get_logs(limit=1)) > 0
