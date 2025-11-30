import inspect
import logging
import os
import sys
from typing import List

from database.schema.log import LogLevel
from manager.storage_manager import StorageManager


class LogManager:
    _instance = None
    storage_manager: StorageManager = None

    def __new__(cls, log_dir=None, storage_manager=None):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
            cls._instance._initialize_logger(log_dir)
            cls._instance.storage_manager = storage_manager
        return cls._instance

    def __init__(self, log_dir=None, storage_manager=None):
        """
        Initialize instance.
        Note: Actual initialization is done in __new__ -> _initialize_logger
        to ensure singleton pattern with one-time setup.
        """
        pass

    def _initialize_logger(self, log_dir=None):
        """Initialize and configure logger"""
        self.logger = logging.getLogger("SafeHome")
        self.log_file_name = "safehome.log"

        # Prevent duplicate handlers if already configured
        if self.logger.handlers:
            return

        self.logger.setLevel(logging.DEBUG)

        # Set log directory
        if log_dir:
            self.log_dir = log_dir
        else:
            # Default: src/log/safehome.log
            base_dir = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
            self.log_dir = os.path.join(base_dir, "log")

        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        log_file = os.path.join(self.log_dir, self.log_file_name)

        # Set format: Severity - Time - File:Line - Function - Message
        formatter = logging.Formatter(
            "[%(levelname)s] [%(asctime)s] [%(filename)s:%(lineno)d] "
            "[%(funcName)s] | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Configure file handler
        try:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            print(f"Failed to create log file handler: {e}")

        # Configure console handler (for development convenience)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def get_logs(self) -> List[str]:
        """
        Get all logs from the log file.

        Returns:
            List[str]: List of log lines from the file.
                      Returns empty list if file doesn't exist or error occurs.
        """
        try:
            log_file_path = os.path.join(self.log_dir, self.log_file_name)

            # Read the log file
            if os.path.exists(log_file_path):
                with open(log_file_path, "r", encoding="utf-8") as f:
                    return f.readlines()
            else:
                return []

        except Exception as e:
            print(f"Failed to read log file: {e}")
            return []

    def _debug(self, message):
        """Log DEBUG level (detailed information for debugging)"""
        self.logger.debug(message, stacklevel=3)

    def _info(self, message):
        """Log INFO level (general information, state changes, etc.)"""
        self.logger.info(message, stacklevel=3)

    def _warning(self, message):
        """Log WARNING level (situations requiring attention,
        unexpected values, etc.)"""
        self.logger.warning(message, stacklevel=3)

    def _error(self, message):
        """Log ERROR level (function failures, exceptions, etc.)"""
        self.logger.error(message, stacklevel=3)

    def _critical(self, message):
        """Log CRITICAL level (severe system errors,
        intrusion detection, etc.)"""
        self.logger.critical(message, stacklevel=3)

    def log(self, message: str, level: LogLevel = LogLevel.INFO) -> None:
        """Log a message with a level"""
        match level:
            case LogLevel.DEBUG:
                self._debug(message)
            case LogLevel.INFO:
                self._info(message)
            case LogLevel.WARNING:
                self._warning(message)
            case LogLevel.ERROR:
                self._error(message)
            case LogLevel.CRITICAL:
                self._critical(message)
            case _:
                raise ValueError(f"Invalid log level: {level}")

        # Capture caller metadata (file, function, line) for DB storage
        try:
            frame = inspect.currentframe()
            caller = frame.f_back.f_back if frame and frame.f_back else None
            filename = (
                os.path.basename(caller.f_code.co_filename) if caller else ""
            )
            function_name = caller.f_code.co_name if caller else ""
            line_number = caller.f_lineno if caller else 0
        except Exception:
            filename = ""
            function_name = ""
            line_number = 0

        self.storage_manager.insert_log(
            level.value,
            message,
            filename=filename,
            function_name=function_name,
            line_number=line_number,
        )
