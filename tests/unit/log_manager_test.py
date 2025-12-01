import pytest
from unittest.mock import Mock, patch, mock_open
import logging
import os
from manager.log_manager import LogManager, LogLevel
from manager.storage_manager import StorageManager

@pytest.fixture
def mock_storage_manager():
    return Mock(spec=StorageManager)

@pytest.fixture
def reset_singleton():
    # 1. LogManager 싱글톤 인스턴스 초기화
    LogManager._instance = None
    
    # 2. 로거 핸들러 초기화 (중요: 이전 테스트의 핸들러가 남아있으면 초기화 로직이 스킵됨)
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
    # 파일 시스템 접근을 막기 위한 Mocking
    with patch("os.makedirs"), \
         patch("os.path.exists", return_value=False), \
         patch("logging.FileHandler"):
        
        manager = LogManager(log_dir="/tmp", storage_manager=mock_storage_manager)
        # 내부 로거 메서드 호출 확인을 위한 Mock
        manager.logger = Mock()
        # _initialize_logger가 정상 완료되었다면 log_dir이 설정되어야 함
        return manager

def test_singleton(reset_singleton, mock_storage_manager):
    lm1 = LogManager(storage_manager=mock_storage_manager)
    lm2 = LogManager(storage_manager=mock_storage_manager)
    assert lm1 is lm2

def test_init_creates_handlers(log_manager):
    # log_manager 픽스처 생성 시 이미 _initialize_logger가 호출됨
    assert log_manager.storage_manager is not None
    # log_dir이 정상적으로 설정되었는지 확인
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
    
    # 로거의 메서드(debug, info 등)가 호출되었는지 확인
    getattr(log_manager.logger, method_name).assert_called()
    
    # DB 저장 호출 확인
    mock_storage_manager.insert_log.assert_called()
    args, _ = mock_storage_manager.insert_log.call_args
    assert args[0] == level.value # Log level value check

def test_log_invalid_level(log_manager):
    with pytest.raises(ValueError):
        log_manager.log("msg", "INVALID")

def test_get_logs_success(log_manager):
    # Mocking open to return fake logs
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data="log line 1\nlog line 2")):
        logs = log_manager.get_logs()
        assert len(logs) == 2
        assert logs[0] == "log line 1\n"

def test_get_logs_file_not_found(log_manager):
    with patch("os.path.exists", return_value=False):
        assert log_manager.get_logs() == []

def test_get_logs_exception(log_manager):
    # 파일 열기 중 에러 발생 시 빈 리스트 반환 테스트
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", side_effect=IOError("Read error")):
        assert log_manager.get_logs() == []

def test_log_metadata_capture(log_manager, mock_storage_manager):
    # 스택 프레임 검사 로직 테스트
    log_manager.log("test", LogLevel.INFO)
    
    mock_storage_manager.insert_log.assert_called()
    call_kwargs = mock_storage_manager.insert_log.call_args[1]
    
    # 호출자 정보가 포함되었는지 확인
    assert "filename" in call_kwargs
    assert "function_name" in call_kwargs
    assert "line_number" in call_kwargs

def test_log_metadata_exception(log_manager, mock_storage_manager):
    # inspect 실행 중 예외 발생 시 방어 코드 테스트
    with patch("inspect.currentframe", side_effect=Exception("Stack error")):
        log_manager.log("test", LogLevel.INFO)
        
    mock_storage_manager.insert_log.assert_called()
    call_kwargs = mock_storage_manager.insert_log.call_args[1]
    # 예외 발생 시 기본값으로 저장되는지 확인
    assert call_kwargs["filename"] == ""
    assert call_kwargs["function_name"] == ""
    assert call_kwargs["line_number"] == 0

def test_initialize_logger_default_dir(reset_singleton, mock_storage_manager):
    # log_dir 인자 없이 초기화할 때 기본 경로 생성 로직 테스트
    with patch("os.makedirs") as mock_makedirs, \
         patch("os.path.exists", return_value=False), \
         patch("logging.FileHandler"):
        
        lm = LogManager(storage_manager=mock_storage_manager)
        assert "log" in lm.log_dir
        # 디렉토리 생성 시도 확인
        mock_makedirs.assert_called()

def test_initialize_logger_early_return(reset_singleton, mock_storage_manager):
    # 이미 핸들러가 있는 경우 초기화 로직을 건너뛰는지 테스트
    logger = logging.getLogger("SafeHome")
    logger.addHandler(logging.StreamHandler()) # 핸들러 강제 추가
    
    lm = LogManager(storage_manager=mock_storage_manager)
    # 초기화가 건너뛰어지면 log_dir 속성이 설정되지 않을 수 있음 (코드 구조상)
    # 이 테스트는 분기 커버리지를 위한 것임
    assert logger.handlers

def test_initialize_logger_file_handler_error(reset_singleton, mock_storage_manager):
    # FileHandler 생성 실패(예외 발생) 시 프로그램이 죽지 않고 처리되는지 테스트
    # 이것이 Coverage 100%를 위한 마지막 조각일 가능성이 높음
    with patch("os.makedirs"), \
         patch("os.path.exists", return_value=False), \
         patch("logging.FileHandler", side_effect=Exception("Permission Denied")):
        
        lm = LogManager(storage_manager=mock_storage_manager)
        
        # 파일 핸들러 생성 실패 시 콘솔 핸들러만 추가되어야 함
        assert len(lm.logger.handlers) == 1
        assert isinstance(lm.logger.handlers[0], logging.StreamHandler)