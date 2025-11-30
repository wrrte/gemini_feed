from unittest.mock import MagicMock, patch

import pytest

from core.system import System
from database.schema.log import LogLevel
from database.schema.sensor import SensorType

"""Unit tests for System class"""


class TestSystem:
    """Test cases for System class"""

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    def test_system_initialization_with_defaults(
        self, mock_ecs, mock_webapp, mock_cp
    ):
        """Test System initialization with default parameters"""
        system = System()

        assert system.reset_database is False
        assert system.auto_login is False
        assert system.storage_manager is None
        assert system.log_manager is None
        assert system.sensor_manager is None
        assert system.login_manager is None
        assert system.configuration_manager is None
        assert system.camera_manager is None
        assert system.alarm_manager is None
        assert system.external_call_service is not None
        mock_ecs.assert_called_once()
        mock_cp.assert_called_once()
        mock_webapp.assert_called_once()

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    def test_system_initialization_with_both_true(
        self, mock_ecs, mock_webapp, mock_cp
    ):
        """Test System initialization with
        reset_database=True and auto_login=True"""
        system = System(reset_database=True, auto_login=True)

        assert system.reset_database is True
        assert system.auto_login is True

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    def test_set_reset_database(self, mock_ecs, mock_webapp, mock_cp):
        """Test set_reset_database(bool) method"""
        system = System()

        system.set_reset_database(True)

        assert system.reset_database is True

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    def test_arrange_windows(self, mock_ecs, mock_webapp, mock_cp):
        """Test _arrange_windows() method sets correct window positions"""
        mock_cp_instance = MagicMock()
        mock_webapp_instance = MagicMock()
        mock_cp.return_value = mock_cp_instance
        mock_webapp.return_value = mock_webapp_instance

        system = System()
        system._arrange_windows()

        # Verify ControlPanel position
        mock_cp_instance.geometry.assert_called_once_with("+100+100")

        # Verify WebApp position
        mock_webapp_instance.geometry.assert_called_once_with("+625+100")

        # Verify Z-order
        mock_webapp_instance.lift.assert_called_once()
        mock_cp_instance.lift.assert_called_once()
        mock_cp_instance.focus_force.assert_called_once()

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    @patch("core.system.StorageManager")
    @patch("core.system.LogManager")
    @patch("core.system.AlarmManager")
    @patch("core.system.SensorManager")
    @patch("core.system.CameraManager")
    @patch("core.system.LoginManager")
    @patch("core.system.ConfigurationManager")
    @patch("core.system.Alarm")
    def test_initialize_managers_success(
        self,
        mock_alarm,
        mock_config_mgr,
        mock_login_mgr,
        mock_camera_mgr,
        mock_sensor_mgr,
        mock_alarm_mgr,
        mock_log_mgr,
        mock_storage_mgr,
        mock_ecs,
        mock_webapp,
        mock_cp,
    ):
        """Test _initialize_managers() method
        successfully initializes all managers"""
        mock_storage_instance = MagicMock()
        mock_storage_instance.get_all_sensors.return_value = []
        mock_storage_mgr.return_value = mock_storage_instance

        mock_log_instance = MagicMock()
        mock_log_mgr.return_value = mock_log_instance

        system = System()
        system._initialize_managers()

        # Verify StorageManager initialized
        mock_storage_mgr.assert_called_once_with(reset_database=False)
        assert system.storage_manager is not None

        # Verify LogManager initialized
        mock_log_mgr.assert_called_once_with(
            storage_manager=mock_storage_instance
        )
        assert system.log_manager is not None

        # Verify log messages
        assert mock_log_instance.log.call_count >= 7

        # Verify AlarmManager initialized
        mock_alarm.assert_called_once()
        mock_alarm_mgr.assert_called_once()
        assert system.alarm_manager is not None

        # Verify SensorManager initialized
        mock_sensor_mgr.assert_called_once()
        assert system.sensor_manager is not None

        # Verify CameraManager initialized
        mock_camera_mgr.assert_called_once_with(
            storage_manager=mock_storage_instance
        )
        assert system.camera_manager is not None

        # Verify LoginManager initialized
        mock_login_mgr.assert_called_once_with(
            storage_manager=mock_storage_instance
        )
        assert system.login_manager is not None

        # Verify ConfigurationManager initialized
        mock_config_mgr.assert_called_once()
        assert system.configuration_manager is not None

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    @patch("core.system.StorageManager")
    @patch("builtins.print")
    @patch("builtins.exit")
    def test_initialize_managers_failure(
        self,
        mock_exit,
        mock_print,
        mock_storage_mgr,
        mock_ecs,
        mock_webapp,
        mock_cp,
    ):
        """Test _initialize_managers() handles exceptions properly"""
        mock_storage_mgr.side_effect = Exception("Storage error")

        mock_cp_instance = MagicMock()
        mock_cp.return_value = mock_cp_instance

        system = System()

        # Mock destroy method to prevent actual GUI destruction
        system.destroy = MagicMock()

        # Set log_manager to a mock so the error path can log
        # (since hasattr checks will find it but it's None by default)
        mock_log = MagicMock()
        system.log_manager = mock_log

        system._initialize_managers()

        # Verify error handling
        mock_print.assert_called()
        mock_log.log.assert_called_once()
        system.destroy.assert_called_once()
        mock_exit.assert_called_once_with(1)

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    @patch("core.system.StorageManager")
    @patch("core.system.LogManager")
    @patch("core.system.AlarmManager")
    @patch("core.system.SensorManager")
    @patch("core.system.CameraManager")
    @patch("core.system.LoginManager")
    @patch("core.system.ConfigurationManager")
    @patch("core.system.Alarm")
    def test_turn_on_success(
        self,
        mock_alarm,
        mock_config_mgr,
        mock_login_mgr,
        mock_camera_mgr,
        mock_sensor_mgr,
        mock_alarm_mgr,
        mock_log_mgr,
        mock_storage_mgr,
        mock_ecs,
        mock_webapp,
        mock_cp,
    ):
        """Test turn_on() method returns True on success"""
        mock_storage_instance = MagicMock()
        mock_storage_instance.get_all_sensors.return_value = []
        mock_storage_mgr.return_value = mock_storage_instance

        mock_sensor_mgr_instance = MagicMock()
        mock_sensor_mgr.return_value = mock_sensor_mgr_instance

        mock_webapp_instance = MagicMock()
        mock_cp_instance = MagicMock()
        mock_webapp.return_value = mock_webapp_instance
        mock_cp.return_value = mock_cp_instance

        system = System()
        result = system.turn_on()

        assert result is True
        mock_webapp_instance.set_managers.assert_called_once()
        mock_cp_instance.set_managers.assert_called_once()
        mock_sensor_mgr_instance.start_monitoring.assert_called_once()

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    @patch("core.system.StorageManager")
    @patch("builtins.print")
    def test_turn_on_failure(
        self, mock_print, mock_storage_mgr, mock_ecs, mock_webapp, mock_cp
    ):
        """Test turn_on() method returns False on failure"""
        mock_storage_mgr.side_effect = Exception("Initialization error")

        system = System()
        result = system.turn_on()

        assert result is False
        mock_print.assert_called()

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    def test_turn_off(self, mock_ecs, mock_webapp, mock_cp):
        """Test turn_off() method returns True and calls cleanup"""
        system = System()
        system.cleanup = MagicMock()

        result = system.turn_off()

        assert result is True
        system.cleanup.assert_called_once()

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    @patch("core.system.show_toast")
    def test_external_call_with_both_phone_numbers_success(
        self, mock_toast, mock_ecs, mock_webapp, mock_cp
    ):
        """Test external_call() method with both phone numbers successful"""
        mock_ecs_instance = MagicMock()
        mock_ecs_instance.call.return_value = True
        mock_ecs.return_value = mock_ecs_instance

        mock_webapp_instance = MagicMock()
        mock_webapp.return_value = mock_webapp_instance

        mock_config_mgr = MagicMock()
        mock_system_settings = MagicMock()
        mock_system_settings.get_panic_phone_number.return_value = "123456789"
        mock_system_settings.get_homeowner_phone_number.return_value = (
            "987654321"
        )
        mock_config_mgr.system_settings = mock_system_settings

        system = System()
        system.configuration_manager = mock_config_mgr

        result = system.external_call()

        assert result == ["123456789", "987654321"]
        assert mock_ecs_instance.call.call_count == 2
        mock_toast.assert_called_once_with(
            mock_webapp_instance,
            "Emergency called to 123456789, 987654321",
            duration_ms=5000,
        )

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    @patch("core.system.show_toast")
    def test_external_call_with_one_phone_number_success(
        self, mock_toast, mock_ecs, mock_webapp, mock_cp
    ):
        """Test external_call() method with one phone number successful"""
        mock_ecs_instance = MagicMock()
        mock_ecs_instance.call.side_effect = [True, False]
        mock_ecs.return_value = mock_ecs_instance

        mock_webapp_instance = MagicMock()
        mock_webapp.return_value = mock_webapp_instance

        mock_config_mgr = MagicMock()
        mock_system_settings = MagicMock()
        mock_system_settings.get_panic_phone_number.return_value = "123456789"
        mock_system_settings.get_homeowner_phone_number.return_value = (
            "987654321"
        )
        mock_config_mgr.system_settings = mock_system_settings

        system = System()
        system.configuration_manager = mock_config_mgr

        result = system.external_call()

        assert result == ["123456789"]
        mock_toast.assert_called_once_with(
            mock_webapp_instance,
            "Emergency called to 123456789",
            duration_ms=5000,
        )

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    @patch("core.system.show_toast")
    def test_external_call_with_no_phone_numbers(
        self, mock_toast, mock_ecs, mock_webapp, mock_cp
    ):
        """Test external_call() method with no phone numbers"""
        mock_ecs_instance = MagicMock()
        mock_ecs.return_value = mock_ecs_instance

        mock_webapp_instance = MagicMock()
        mock_webapp.return_value = mock_webapp_instance

        mock_config_mgr = MagicMock()
        mock_system_settings = MagicMock()
        mock_system_settings.get_panic_phone_number.return_value = None
        mock_system_settings.get_homeowner_phone_number.return_value = None
        mock_config_mgr.system_settings = mock_system_settings

        system = System()
        system.configuration_manager = mock_config_mgr

        result = system.external_call()

        assert result == []
        mock_ecs_instance.call.assert_not_called()
        mock_toast.assert_called_once_with(
            mock_webapp_instance,
            "Emergency call failed. Please try again.",
            duration_ms=5000,
        )

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    @patch("core.system.show_toast")
    def test_external_call_with_all_calls_failing(
        self, mock_toast, mock_ecs, mock_webapp, mock_cp
    ):
        """Test external_call() method with all calls failing"""
        mock_ecs_instance = MagicMock()
        mock_ecs_instance.call.return_value = False
        mock_ecs.return_value = mock_ecs_instance

        mock_webapp_instance = MagicMock()
        mock_webapp.return_value = mock_webapp_instance

        mock_config_mgr = MagicMock()
        mock_system_settings = MagicMock()
        mock_system_settings.get_panic_phone_number.return_value = "123456789"
        mock_system_settings.get_homeowner_phone_number.return_value = (
            "987654321"
        )
        mock_config_mgr.system_settings = mock_system_settings

        system = System()
        system.configuration_manager = mock_config_mgr

        result = system.external_call()

        assert result == []
        assert mock_ecs_instance.call.call_count == 2
        mock_toast.assert_called_once_with(
            mock_webapp_instance,
            "Emergency call failed. Please try again.",
            duration_ms=5000,
        )

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    def test_handle_intrusion_when_already_ringing(
        self, mock_ecs, mock_webapp, mock_cp
    ):
        """Test handle_intrusion(int, SensorType) when alarm is ringing"""
        system = System()
        system.alarm_manager = MagicMock()
        system.alarm_manager.is_ringing.return_value = True

        system.handle_intrusion(1, SensorType.MOTION_DETECTOR_SENSOR)

        system.alarm_manager.ring_alarm.assert_not_called()

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    def test_handle_intrusion_when_not_ringing(
        self, mock_ecs, mock_webapp, mock_cp
    ):
        """Test handle_intrusion(int, SensorType) when alarm is not ringing"""
        mock_cp_instance = MagicMock()
        mock_cp.return_value = mock_cp_instance

        system = System()
        system.alarm_manager = MagicMock()
        system.alarm_manager.is_ringing.return_value = False
        system.log_manager = MagicMock()

        system.handle_intrusion(1, SensorType.MOTION_DETECTOR_SENSOR)

        expected_msg = (
            "INTRUSION DETECTED: Sensor 1 "
            "(Type: MOTION_DETECTOR_SENSOR) triggered!"
        )
        system.log_manager.log.assert_called_once_with(
            expected_msg,
            level=LogLevel.CRITICAL,
        )
        system.alarm_manager.ring_alarm.assert_called_once()
        mock_cp_instance.after.assert_called_once_with(
            0, mock_cp_instance.start_count_down_for_external_call
        )

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    @patch("builtins.print")
    def test_handle_intrusion_without_control_panel(
        self, mock_print, mock_ecs, mock_webapp, mock_cp
    ):
        """Test handle_intrusion(int, SensorType) without control panel"""
        system = System()
        system.alarm_manager = MagicMock()
        system.alarm_manager.is_ringing.return_value = False
        system.log_manager = MagicMock()
        system.control_panel = None

        system.handle_intrusion(2, SensorType.WINDOOR_SENSOR)

        system.alarm_manager.ring_alarm.assert_called_once()
        mock_print.assert_called_once_with("ControlPanel is not initialized")

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    def test_clean_up_managers_with_all_managers(
        self, mock_ecs, mock_webapp, mock_cp
    ):
        """Test _clean_up_managers() method with all managers initialized"""
        system = System()

        # Set up mock managers
        mock_config = MagicMock()
        mock_storage = MagicMock()
        system.configuration_manager = mock_config
        system.login_manager = MagicMock()
        system.sensor_manager = MagicMock()
        system.storage_manager = mock_storage
        system.log_manager = MagicMock()
        system.camera_manager = MagicMock()

        system._clean_up_managers()

        mock_config.clean_up_configuration_manager.assert_called_once()
        mock_storage.clean_up.assert_called_once()

        assert system.configuration_manager is None
        assert system.login_manager is None
        assert system.sensor_manager is None
        assert system.storage_manager is None
        assert system.log_manager is None
        assert system.camera_manager is None

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    def test_clean_up_managers_with_no_managers(
        self, mock_ecs, mock_webapp, mock_cp
    ):
        """Test _clean_up_managers() method with no managers initialized"""
        system = System()

        # Delete attributes to simulate no managers
        if hasattr(system, "configuration_manager"):
            delattr(system, "configuration_manager")
        if hasattr(system, "login_manager"):
            delattr(system, "login_manager")
        if hasattr(system, "sensor_manager"):
            delattr(system, "sensor_manager")
        if hasattr(system, "storage_manager"):
            delattr(system, "storage_manager")
        if hasattr(system, "log_manager"):
            delattr(system, "log_manager")
        if hasattr(system, "camera_manager"):
            delattr(system, "camera_manager")

        # Should not raise any exceptions
        system._clean_up_managers()

        # All managers should not exist as attributes
        assert (
            not hasattr(system, "configuration_manager")
            or system.configuration_manager is None
        )
        assert (
            not hasattr(system, "login_manager")
            or system.login_manager is None
        )
        assert (
            not hasattr(system, "sensor_manager")
            or system.sensor_manager is None
        )
        assert (
            not hasattr(system, "storage_manager")
            or system.storage_manager is None
        )
        assert not hasattr(system, "log_manager") or system.log_manager is None
        assert (
            not hasattr(system, "camera_manager")
            or system.camera_manager is None
        )

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    @patch("builtins.print")
    def test_clean_up_managers_with_exception(
        self, mock_print, mock_ecs, mock_webapp, mock_cp
    ):
        """Test _clean_up_managers() handles exceptions"""
        system = System()
        system.configuration_manager = MagicMock()
        cleanup_method = (
            system.configuration_manager.clean_up_configuration_manager
        )
        cleanup_method.side_effect = Exception("Cleanup error")
        system.log_manager = MagicMock()

        system._clean_up_managers()

        mock_print.assert_called()
        system.log_manager.error.assert_called_once()

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    def test_cleanup_with_all_components(self, mock_ecs, mock_webapp, mock_cp):
        """Test cleanup() method with all components initialized"""
        mock_webapp_instance = MagicMock()
        mock_webapp.return_value = mock_webapp_instance

        system = System()
        system.sensor_manager = MagicMock()
        system.login_manager = MagicMock()
        system._clean_up_managers = MagicMock()

        system.cleanup()

        system.sensor_manager.stop_monitoring.assert_called_once()
        system.login_manager.logout_web.assert_called_once()
        system.login_manager.logout_panel.assert_called_once()
        system._clean_up_managers.assert_called_once()
        mock_webapp_instance.clean_up_managers.assert_called_once()
        mock_webapp_instance.draw_page.assert_called_once()

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    @patch("builtins.print")
    def test_cleanup_with_exception(
        self, mock_print, mock_ecs, mock_webapp, mock_cp
    ):
        """Test cleanup() method handles exceptions"""
        system = System()
        system.sensor_manager = MagicMock()
        system.sensor_manager.stop_monitoring.side_effect = Exception(
            "Stop error"
        )
        system.log_manager = MagicMock()

        system.cleanup()

        mock_print.assert_called()
        system.log_manager.error.assert_called_once()

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    @patch("builtins.print")
    def test_execute_login_success(
        self, mock_print, mock_ecs, mock_webapp, mock_cp
    ):
        """Test _execute_login() method with successful login"""
        mock_webapp_instance = MagicMock()
        mock_webapp.return_value = mock_webapp_instance

        system = System()
        system.login_manager = MagicMock()
        system.login_manager.login_web.return_value = True

        system._execute_login()

        system.login_manager.login_web.assert_called_once_with(
            "master", "12345678"
        )
        mock_webapp_instance.switch_to_main.assert_called_once()
        mock_print.assert_called_with("Logged in as: master")

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    @patch("builtins.print")
    def test_execute_login_failure(
        self, mock_print, mock_ecs, mock_webapp, mock_cp
    ):
        """Test _execute_login() method with failed login"""
        mock_webapp_instance = MagicMock()
        mock_webapp.return_value = mock_webapp_instance

        system = System()
        system.login_manager = MagicMock()
        system.login_manager.login_web.return_value = False

        system._execute_login()

        system.login_manager.login_web.assert_called_once_with(
            "master", "12345678"
        )
        mock_webapp_instance.switch_to_main.assert_not_called()
        mock_print.assert_called_with(
            "Auto-login failed: Invalid ID 'master'."
        )

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    def test_run_without_auto_login(self, mock_ecs, mock_webapp, mock_cp):
        """Test run() method without auto login"""
        mock_cp_instance = MagicMock()
        mock_cp.return_value = mock_cp_instance

        system = System(auto_login=False)
        system._arrange_windows = MagicMock()

        system.run()

        system._arrange_windows.assert_called_once()
        mock_cp_instance.input_handler.handle_button_press.assert_not_called()
        mock_cp_instance.after.assert_not_called()
        mock_cp_instance.mainloop.assert_called_once()

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    @patch("builtins.print")
    def test_run_with_auto_login(
        self, mock_print, mock_ecs, mock_webapp, mock_cp
    ):
        """Test run() method with auto login"""
        mock_cp_instance = MagicMock()
        mock_cp.return_value = mock_cp_instance

        system = System(auto_login=True)
        system._arrange_windows = MagicMock()

        system.run()
        input_handler = mock_cp_instance.input_handler
        system._arrange_windows.assert_called_once()
        mock_print.assert_called_with("--- Auto Login Sequence Started ---")
        input_handler.handle_button_press.assert_called_once_with("1")
        mock_cp_instance.after.assert_called_once_with(
            2500, system._execute_login
        )
        mock_cp_instance.mainloop.assert_called_once()

    @patch("core.system.ControlPanel")
    @patch("core.system.WebApp")
    @patch("core.system.ExternalCallService")
    def test_destroy(self, mock_ecs, mock_webapp, mock_cp):
        """Test destroy() method calls cleanup"""
        system = System()
        system.cleanup = MagicMock()

        # destroy() calls cleanup and then super().destroy()
        # Since System doesn't inherit from anything except object,
        # super().destroy() will raise AttributeError
        with pytest.raises(AttributeError):
            system.destroy()

        system.cleanup.assert_called_once()
