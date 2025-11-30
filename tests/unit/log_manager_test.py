import os
import shutil
from pathlib import Path

import pytest

from manager.log_manager import LogLevel, LogManager
from manager.storage_manager import StorageManager

current_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.abspath(os.path.join(current_dir, '../log'))
db_dir = os.path.abspath(os.path.join(current_dir, '../../database'))


@pytest.fixture(autouse=True)
def tmp_path(request):
    """
    Override tmp_path to use a fixed directory for easier inspection.
    Path: src/tests/log/test_function_name/
    """
    # Sub-directory for specific test function
    func_name = request.function.__name__
    path = os.path.join(log_dir, func_name)

    # Clean up previous test results
    if os.path.exists(path):
        shutil.rmtree(path)
        os.makedirs(path)

    return Path(path)


@pytest.fixture(autouse=True)
def reset_singleton(request):
    """
    Initialize the singleton instance of LogManager before and after each test.
    This prevents interference between tests.
    """
    # Setup: Initialize instance
    LogManager._instance = None

    yield

    # Teardown: Clean up logger handlers and initialize instance
    if LogManager._instance and hasattr(LogManager._instance, 'logger'):
        logger = LogManager._instance.logger
        handlers = logger.handlers[:]
        for handler in handlers:
            handler.close()
            logger.removeHandler(handler)

    LogManager._instance = None

    # Delete log directory
    if os.path.exists(log_dir):
        shutil.rmtree(log_dir)


@pytest.fixture(autouse=True)
def clear_logs_table():
    storage_manager = StorageManager(db_file_name='safehome_test.db')
    storage_manager.execute_query("DELETE FROM logs")
    yield


def get_log_manager(log_dir: Path) -> LogManager:
    storage_manager = StorageManager(db_file_name='safehome_test.db')
    return LogManager(log_dir=str(log_dir), storage_manager=storage_manager)


def test_singleton_behavior(tmp_path):
    """Test if singleton pattern works correctly"""
    log_dir = tmp_path

    manager1 = get_log_manager(log_dir)
    manager2 = get_log_manager(log_dir)

    assert manager1 is manager2
    assert id(manager1) == id(manager2)


def test_log_file_creation(tmp_path):
    """Test if log file is created in the specified path"""
    log_dir = tmp_path

    manager = get_log_manager(log_dir)
    manager.log(message="Test log creation", level=LogLevel.INFO)

    log_file = os.path.join(log_dir, LogManager._instance.log_file_name)
    assert os.path.exists(log_file)
    assert os.path.isfile(log_file)


def test_log_content_format(tmp_path):
    """Test if log content includes required information
    (message, level, function name, line number)"""
    log_dir = tmp_path
    manager = get_log_manager(log_dir)

    test_msg = "Unique test message content"
    manager.log(message=test_msg, level=LogLevel.INFO)

    log_file = os.path.join(log_dir, LogManager._instance.log_file_name)
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check format
    assert test_msg in content
    assert LogLevel.INFO.value in content
    assert "test_log_content_format" in content
    assert "log_manager_test.py:" in content  # File with line number
    import re
    assert re.search(r'log_manager_test\.py:\d+', content) is not None


def test_all_log_levels(tmp_path):
    """Test if all log levels are recorded correctly"""
    log_dir = tmp_path
    manager = get_log_manager(log_dir)

    manager.log(message="Debug message", level=LogLevel.DEBUG)
    manager.log(message="Info message", level=LogLevel.INFO)
    manager.log(message="Warning message", level=LogLevel.WARNING)
    manager.log(message="Error message", level=LogLevel.ERROR)
    manager.log(message="Critical message", level=LogLevel.CRITICAL)

    # test log in file
    log_file = os.path.join(log_dir, LogManager._instance.log_file_name)
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()
    assert LogLevel.DEBUG.value in content and "Debug message" in content
    assert LogLevel.INFO.value in content and "Info message" in content
    assert LogLevel.WARNING.value in content and "Warning message" in content
    assert LogLevel.ERROR.value in content and "Error message" in content
    assert LogLevel.CRITICAL.value in content and "Critical message" in content

    # test log in database
    logs = manager.storage_manager.get_logs(limit=10)
    print(logs)
    assert len(logs) == 5
    assert logs[4]['level'] == LogLevel.DEBUG.value
    assert logs[4]['message'] == "Debug message"
    assert logs[3]['level'] == LogLevel.INFO.value
    assert logs[3]['message'] == "Info message"
    assert logs[2]['level'] == LogLevel.WARNING.value
    assert logs[2]['message'] == "Warning message"
    assert logs[1]['level'] == LogLevel.ERROR.value
    assert logs[1]['message'] == "Error message"
    assert logs[0]['level'] == LogLevel.CRITICAL.value
    assert logs[0]['message'] == "Critical message"


def test_log_directory_auto_creation(tmp_path):
    """Test if log directory is automatically created if it doesn't exist"""
    log_dir = str(tmp_path / "new_dir" / "nested_logs")

    # Start with no directory
    assert not os.path.exists(log_dir)

    get_log_manager(log_dir)

    # Check if directory is created after constructor call
    assert os.path.exists(log_dir)
