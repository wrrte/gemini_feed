import pytest
from unittest.mock import Mock, patch, mock_open
import logging
from manager.log_manager import LogManager, LogLevel
from manager.storage_manager import StorageManager

@pytest.fixture
def mock_storage_manager():
    return Mock(spec=StorageManager)

@pytest.fixture
def reset_singleton():
    LogManager._instance = None
    yield
    LogManager._instance = None

@pytest.fixture
def log_manager(reset_singleton, mock_storage_manager):
    with patch("os.makedirs"), patch("os.path.exists", return_value=False), patch("logging.FileHandler"):
        manager = LogManager(log_dir="/tmp", storage_manager=mock_storage_manager)
        # Mock the internal logger
        manager.logger = Mock()
        return manager

def test_singleton(reset_singleton):
    lm1 = LogManager()
    lm2 = LogManager()
    assert lm1 is lm2

@pytest.mark.parametrize("level, method_name", [
    (LogLevel.DEBUG, "debug"),
    (LogLevel.INFO, "info"),
    (LogLevel.WARNING, "warning"),
    (LogLevel.ERROR, "error"),
    (LogLevel.CRITICAL, "critical")
])
def test_log_levels(log_manager, mock_storage_manager, level, method_name):
    log_manager.log("test msg", level)
    
    # Check logger method called
    getattr(log_manager.logger, method_name).assert_called()
    
    # Check DB insert
    mock_storage_manager.insert_log.assert_called()
    args, _ = mock_storage_manager.insert_log.call_args
    assert args[0] == level.value

def test_log_invalid_level(log_manager):
    with pytest.raises(ValueError):
        log_manager.log("msg", "INVALID")

def test_get_logs(log_manager):
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data="log1\nlog2")):
        logs = log_manager.get_logs()
        assert len(logs) == 2
        assert logs[0] == "log1\n"

def test_get_logs_no_file(log_manager):
    with patch("os.path.exists", return_value=False):
        assert log_manager.get_logs() == []