from typing import List

from core.control_panel.control_panel import ControlPanel
from core.pages.utils import show_toast
from core.web_app import WebApp
from database.schema.log import LogLevel
from database.schema.sensor import SensorType
from device.appliance.alarm import Alarm
from device.sensor import create_sensor_from_schema
from manager.alarm_manager import AlarmManager
from manager.camera_manager import CameraManager
from manager.configuration_manager import ConfigurationManager
from manager.log_manager import LogManager
from manager.login_manager import LoginManager
from manager.sensor_manager import SensorManager
from manager.storage_manager import StorageManager
from service.external_call_service import ExternalCallService


class System:
    def __init__(self, reset_database: bool = False, auto_login: bool = False):
        # initialize variables
        self.reset_database = reset_database
        self.auto_login = auto_login

        # Managers
        self.storage_manager: StorageManager = None
        self.log_manager: LogManager = None
        self.sensor_manager: SensorManager = None
        self.login_manager: LoginManager = None
        self.configuration_manager: ConfigurationManager = None
        self.camera_manager: CameraManager = None
        self.alarm_manager: AlarmManager = None

        # Services
        self.external_call_service: ExternalCallService = ExternalCallService()

        # Control Panel
        self.control_panel = ControlPanel(
            turn_system_on=self.turn_on,
            turn_system_off=self.turn_off,
            set_reset_database=self.set_reset_database,
            external_call=self.external_call,
            login_manager=self.login_manager,
            configuration_manager=self.configuration_manager,
        )

        # Web App
        self.web_app = WebApp(
            master=self.control_panel,
            page_id="WebApp",
            title="SafeHome Web App",
            login_manager=self.login_manager,
            sensor_manager=self.sensor_manager,
            camera_manager=self.camera_manager,
            initially_hidden=False,
        )

    def run(self):
        # Arrange windows
        self._arrange_windows()

        # [Modified] Improved auto-login logic
        if self.auto_login:
            print("--- Auto Login Sequence Started ---")

            # 1. Call the function as if the user pressed the '1'(ON) button.
            #    This function internally calls turn_on() and turns on the LED.
            self.control_panel.input_handler.handle_button_press("1")

            # 2. Wait for the panel to boot up (about 2 seconds)
            # before performing login.
            # Logging in immediately will be rejected because the panel is
            # still 'turning on'.
            self.control_panel.after(2500, self._execute_login)

        # Start main loop
        self.control_panel.mainloop()

    def _execute_login(self):
        """Actual login logic to be executed after panel boot"""
        test_user_id = "master"  # or "admin"
        test_password = "12345678"

        # Attempt login through LoginManager
        if self.login_manager.login_web(test_user_id, test_password):
            print(f"Logged in as: {test_user_id}")
            self.web_app.switch_to_main()
        else:
            print(f"Auto-login failed: Invalid ID '{test_user_id}'.")

    def turn_on(self) -> bool:
        """Turn on the system."""
        try:
            # Initialize managers
            self._initialize_managers()

            # Set managers to the web app
            self.web_app.set_managers(
                sensor_manager=self.sensor_manager,
                camera_manager=self.camera_manager,
                login_manager=self.login_manager,
                configuration_manager=self.configuration_manager,
            )

            # set managers to the control panel
            self.control_panel.set_managers(
                login_manager=self.login_manager,
                configuration_manager=self.configuration_manager,
                alarm_manager=self.alarm_manager,
                sensor_manager=self.sensor_manager,
            )

            # Start sensor monitoring in background
            if self.sensor_manager:
                self.sensor_manager.start_monitoring()

            # Return success
            return True
        except Exception as e:
            print(f"Failed to turn on the system: {e}")
            return False

    def turn_off(self) -> bool:
        """Turn off the system."""
        self.cleanup()
        return True

    def set_reset_database(self, reset_database: bool):
        """Set reset database flag."""
        self.reset_database = reset_database

    def external_call(self) -> List[str]:
        """
        Make an external call to the emergency phone numbers.
        If the call is successful, the phone number is added to the list.

        Returns:
            List[str]: List of successfully called phone numbers
        """
        system_settings = self.configuration_manager.system_settings
        phone_numbers = [
            system_settings.get_panic_phone_number(),
            system_settings.get_homeowner_phone_number(),
        ]
        success_phone_numbers = []

        for phone_number in phone_numbers:
            if not phone_number:
                continue
            if self.external_call_service.call(phone_number):
                success_phone_numbers.append(phone_number)

        # show toast message in web app
        if success_phone_numbers:
            show_toast(
                self.web_app,
                f"Emergency called to {', '.join(success_phone_numbers)}",
                duration_ms=5000,
            )
        else:
            show_toast(
                self.web_app,
                "Emergency call failed. Please try again.",
                duration_ms=5000,
            )
        return success_phone_numbers

    def handle_intrusion(
        self,
        sensor_id: int,
        sensor_type: SensorType,
    ):
        """
        handle intrusion.
        - check if alarm is already ringing
        - log the event
        - ring the alarm
        - make an external call

        Thread-safe: Can be called from background threads.
        GUI updates are scheduled on the main thread using after().
        """
        # if already ringing, return
        if self.alarm_manager.is_ringing():
            return

        # log the event
        if self.log_manager:
            self.log_manager.log(
                f"INTRUSION DETECTED: Sensor {sensor_id} "
                f"(Type: {sensor_type.name}) triggered!",
                level=LogLevel.CRITICAL,
            )

        # ring the alarm
        self.alarm_manager.ring_alarm()

        # start count down for external call (GUI update at main thread)
        if self.control_panel:
            self.control_panel.after(
                0, self.control_panel.start_count_down_for_external_call
            )
        else:
            print("ControlPanel is not initialized")

    def _arrange_windows(self):
        """Arrange ControlPanel and WebApp windows side-by-side."""
        # 1. Set Control Panel position (top-left of screen)
        # Using fixed position instead of calculating screen center for
        # simplicity
        cp_x, cp_y = 100, 100
        self.control_panel.geometry(f"+{cp_x}+{cp_y}")

        # 2. Set WebApp position (to the right of Control Panel)
        # ControlPanel width (505) + margin (20)
        wa_x = cp_x + 505 + 20
        wa_y = cp_y
        self.web_app.geometry(f"+{wa_x}+{wa_y}")

        # 3. Adjust Z-order (Control Panel on top)
        # Lift WebApp first, then ControlPanel on top of it
        self.web_app.lift()
        self.control_panel.lift()

        # 4. Set focus
        self.control_panel.focus_force()

    def _initialize_managers(self):
        """Initialize essential managers on app startup."""
        try:
            # 1. Initialize StorageManager
            self.storage_manager: StorageManager = StorageManager(
                reset_database=self.reset_database
            )

            # 2. Initialize LogManager
            self.log_manager: LogManager = LogManager(
                storage_manager=self.storage_manager
            )
            self.log_manager.log("SafeHome Application started")
            self.log_manager.log("Initializing managers...")
            self.log_manager.log("StorageManager initialized successfully")
            self.log_manager.log("LogManager initialized successfully")

            # initialize alarm manager
            self.alarm_manager = AlarmManager(alarm=Alarm())

            # 3. Initialize SensorManager
            sensors = self.storage_manager.get_all_sensors()
            self.sensor_manager = SensorManager(
                sensor_dict={
                    sensor.sensor_id: create_sensor_from_schema(sensor)
                    for sensor in sensors
                },
                log_manager=self.log_manager,
                external_call=self.external_call,
                handle_intrusion=self.handle_intrusion,
            )
            self.log_manager.log("SensorManager initialized successfully")

            # 3. Initialize CameraManager
            self.camera_manager = CameraManager(
                storage_manager=self.storage_manager
            )
            self.log_manager.log("CameraManager initialized successfully")

            # 4. Initialize LoginManager
            self.login_manager = LoginManager(
                storage_manager=self.storage_manager
            )
            self.log_manager.log("LoginManager initialized successfully")

            # 5. Initialize ConfigurationManager
            self.configuration_manager = ConfigurationManager(
                storage_manager=self.storage_manager,
                sensor_manager=self.sensor_manager,
            )
            self.log_manager.log(
                "ConfigurationManager initialized successfully"
            )

            self.log_manager.log("All managers initialized successfully")

        except Exception as e:
            print(f"Failed to initialize managers: {e}")
            if hasattr(self, "log_manager"):
                self.log_manager.log(
                    LogLevel.ERROR, f"Manager initialization error: {e}"
                )
            # Exit application
            self.destroy()
            exit(1)

    def _clean_up_managers(self):
        """Clean up managers on app termination"""
        try:
            # clean up configuration manager
            if hasattr(self, "configuration_manager"):
                self.configuration_manager.clean_up_configuration_manager()
                self.configuration_manager = None

            # clean up login manager
            if hasattr(self, "login_manager"):
                self.login_manager = None

            # clean up sensor manager
            if hasattr(self, "sensor_manager"):
                self.sensor_manager = None

            # clean up storage manager
            if hasattr(self, "storage_manager"):
                self.storage_manager.clean_up()
                self.storage_manager = None

            # clean up log manager
            if hasattr(self, "log_manager"):
                self.log_manager = None

            # clean up camera manager
            if hasattr(self, "camera_manager"):
                self.camera_manager = None

        except Exception as e:
            print(f"Error during cleanup managers: {e}")
            if hasattr(self, "log_manager"):
                self.log_manager.error(f"Error during cleanup managers: {e}")

    def cleanup(self):
        """Clean up resources on app termination"""
        try:
            # Stop sensor monitoring
            if hasattr(self, "sensor_manager") and self.sensor_manager:
                self.sensor_manager.stop_monitoring()

            # logout
            if hasattr(self, "login_manager") and self.login_manager:
                self.login_manager.logout_web()
                self.login_manager.logout_panel()

            # clean up managers
            self._clean_up_managers()

            # clean up web app managers
            self.web_app.clean_up_managers()

            # draw page (automatically draw login page)
            self.web_app.draw_page()

        except Exception as e:
            print(f"Error during cleanup: {e}")
            if hasattr(self, "log_manager"):
                self.log_manager.error(f"Error during cleanup: {e}")

    def destroy(self):
        """Call cleanup when app window is closed"""
        self.cleanup()
        super().destroy()
