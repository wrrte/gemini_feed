import logging
from unittest.mock import Mock, mock_open, patch

import pytest

from manager.log_manager import LogLevel, LogManager
from manager.storage_manager import StorageManager


@pytest.fixture
def mock_storage_manager():
    return Mock(spec=StorageManager)


@pytest.fixture
def reset_singleton():
    LogManager._instance = None
    logger = logging.getLogger("SafeHome")
    handlers = logger.handlers[:]
    for handler in handlers:
        logger.removeHandler(handler)
        handler.close()
    yield
    LogManager._instance = None


@pytest.fixture
def log_manager(reset_singleton, mock_storage_manager):
    with patch("os.makedirs"), \
            patch("os.path.exists", return_value=False), \
            patch("logging.FileHandler"):
        manager = LogManager(
            log_dir="/tmp", storage_manager=mock_storage_manager)
        manager.logger = Mock()
        return manager


def test_singleton(reset_singleton, mock_storage_manager):
    lm1 = LogManager(storage_manager=mock_storage_manager)
    lm2 = LogManager(storage_manager=mock_storage_manager)
    assert lm1 is lm2


def test_init_creates_handlers(log_manager):
    assert log_manager.storage_manager is not None


@pytest.mark.parametrize("level, method_name", [
    (LogLevel.DEBUG, "debug"), (LogLevel.INFO, "info"),
    (LogLevel.WARNING, "warning"), (LogLevel.ERROR, "error"),
    (LogLevel.CRITICAL, "critical")
])
def test_log_methods(log_manager, mock_storage_manager, level, method_name):
    log_manager.log("test msg", level)
    getattr(log_manager.logger, method_name).assert_called()
    mock_storage_manager.insert_log.assert_called()


def test_log_invalid_level(log_manager):
    with pytest.raises(ValueError):
        log_manager.log("msg", "INVALID")


def test_get_logs_success(log_manager):
    with patch("os.path.exists", return_value=True), \
            patch("builtins.open",
                  mock_open(read_data="log line 1\nlog line 2")):
        logs = log_manager.get_logs()
        assert len(logs) == 2


def test_get_logs_file_not_found(log_manager):
    with patch("os.path.exists", return_value=False):
        assert log_manager.get_logs() == []


def test_get_logs_read_exception(log_manager):
    with patch("os.path.exists", return_value=True), \
            patch("builtins.open", side_effect=IOError("Read error")):
        assert log_manager.get_logs() == []


def test_log_metadata_exception(log_manager, mock_storage_manager):
    # Simulate exception during stack frame inspection
    with patch("inspect.currentframe", side_effect=Exception("Stack error")):
        log_manager.log("test", LogLevel.INFO)

    mock_storage_manager.insert_log.assert_called()
    call_kwargs = mock_storage_manager.insert_log.call_args[1]
    assert call_kwargs["filename"] == ""
    assert call_kwargs["function_name"] == ""


def test_initialize_logger_file_handler_error(
        reset_singleton, mock_storage_manager):
    # Simulate failure to create file handler
    with patch("os.makedirs"), \
            patch("os.path.exists", return_value=False), \
            patch("logging.FileHandler",
                  side_effect=Exception("Permission Denied")):
        lm = LogManager(storage_manager=mock_storage_manager)
        # Should fall back to stream handler only
        assert len(lm.logger.handlers) == 1
        assert isinstance(lm.logger.handlers[0], logging.StreamHandler)


def test_initialize_logger_already_configured(
        reset_singleton, mock_storage_manager):
    # Simulate logger already having handlers
    logger = logging.getLogger("SafeHome")
    logger.addHandler(logging.StreamHandler())

    lm = LogManager(storage_manager=mock_storage_manager)
    # Shouldn't add more handlers
    assert len(lm.logger.handlers) == 1
