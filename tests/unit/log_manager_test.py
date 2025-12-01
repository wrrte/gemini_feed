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

    # Teardown
    LogManager._instance = None
    handlers = logger.handlers[:]
    for handler in handlers:
        logger.removeHandler(handler)
        handler.close()


@pytest.fixture
def log_manager(reset_singleton, mock_storage_manager):
    with patch("os.makedirs"), \
            patch("os.path.exists", return_value=False), \
            patch("logging.FileHandler"):

        manager = LogManager(
            log_dir="/tmp",
            storage_manager=mock_storage_manager)
        manager.logger = Mock()
        return manager


def test_singleton(reset_singleton, mock_storage_manager):
    lm1 = LogManager(storage_manager=mock_storage_manager)
    lm2 = LogManager(storage_manager=mock_storage_manager)
    assert lm1 is lm2


def test_init_creates_handlers(log_manager):
    assert log_manager.storage_manager is not None
    assert hasattr(log_manager, 'log_dir')


@pytest.mark.parametrize("level, method_name", [
    (LogLevel.DEBUG, "debug"),
    (LogLevel.INFO, "info"),
    (LogLevel.WARNING, "warning"),
    (LogLevel.ERROR, "error"),
    (LogLevel.CRITICAL, "critical")
])
def test_log_methods(log_manager, mock_storage_manager, level, method_name):
    log_manager.log("test msg", level)

    getattr(log_manager.logger, method_name).assert_called()

    mock_storage_manager.insert_log.assert_called()
    args, _ = mock_storage_manager.insert_log.call_args
    assert args[0] == level.value  # Log level value check


def test_log_invalid_level(log_manager):
    with pytest.raises(ValueError):
        log_manager.log("msg", "INVALID")


def test_get_logs_success(log_manager):
    # Mocking open to return fake logs
    with patch("os.path.exists", return_value=True), \
            patch(
                "builtins.open",
                mock_open(read_data="log line 1\nlog line 2")):
        logs = log_manager.get_logs()
        assert len(logs) == 2
        assert logs[0] == "log line 1\n"


def test_get_logs_file_not_found(log_manager):
    with patch("os.path.exists", return_value=False):
        assert log_manager.get_logs() == []


def test_get_logs_exception(log_manager):
    with patch("os.path.exists", return_value=True), \
            patch("builtins.open", side_effect=IOError("Read error")):
        assert log_manager.get_logs() == []


def test_log_metadata_capture(log_manager, mock_storage_manager):
    log_manager.log("test", LogLevel.INFO)

    mock_storage_manager.insert_log.assert_called()
    call_kwargs = mock_storage_manager.insert_log.call_args[1]

    assert "filename" in call_kwargs
    assert "function_name" in call_kwargs
    assert "line_number" in call_kwargs


def test_log_metadata_exception(log_manager, mock_storage_manager):
    with patch("inspect.currentframe", side_effect=Exception("Stack error")):
        log_manager.log("test", LogLevel.INFO)

    mock_storage_manager.insert_log.assert_called()
    call_kwargs = mock_storage_manager.insert_log.call_args[1]
    assert call_kwargs["filename"] == ""
    assert call_kwargs["function_name"] == ""
    assert call_kwargs["line_number"] == 0


def test_initialize_logger_default_dir(reset_singleton, mock_storage_manager):
    with patch("os.makedirs") as mock_makedirs, \
            patch("os.path.exists", return_value=False), \
            patch("logging.FileHandler"):

        lm = LogManager(storage_manager=mock_storage_manager)
        assert "log" in lm.log_dir
        mock_makedirs.assert_called()


def test_initialize_logger_early_return(
        reset_singleton,
        mock_storage_manager):
    logger = logging.getLogger("SafeHome")
    logger.addHandler(logging.StreamHandler())

    assert logger.handlers


def test_initialize_logger_file_handler_error(
        reset_singleton, mock_storage_manager):
    with patch("os.makedirs"), \
            patch("os.path.exists", return_value=False), \
            patch(
                "logging.FileHandler",
                side_effect=Exception("Permission Denied")):

        lm = LogManager(storage_manager=mock_storage_manager)

        assert len(lm.logger.handlers) == 1
        assert isinstance(lm.logger.handlers[0], logging.StreamHandler)
