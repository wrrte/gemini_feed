from datetime import datetime
from typing import Optional

from database.schema.system_setting import SystemSettingSchema


class SystemSettings:
    """
    Reads, maintains and writes phone number of monitoring service,
    phone number of homeowner, system lock time, and delay time before
    alarming.
    """

    def __init__(
        self,
        system_setting_id: int,
        panic_phone_number: Optional[str] = None,
        homeowner_phone_number: Optional[str] = None,
        system_lock_time: Optional[int] = None,
        alarm_delay_time: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """Initialize SystemSettings."""
        self.system_setting_id = system_setting_id
        self.panic_phone_number = panic_phone_number
        self.homeowner_phone_number = homeowner_phone_number
        self.system_lock_time = system_lock_time
        self.alarm_delay_time = alarm_delay_time

    # Panic Phone Number
    def get_panic_phone_number(self) -> Optional[str]:
        """
        Get panic phone number (monitoring service).

        Returns:
            str: Phone number or None if not set
        """
        return self.panic_phone_number

    def set_panic_phone_number(self, phone_number: str) -> bool:
        """
        Set panic phone number (monitoring service).
        Args:
            phone_number (str): Phone number to set

        Returns:
            bool: True if successful, False otherwise
        """
        if not isinstance(phone_number, str):
            return False
        self.panic_phone_number = phone_number
        return True

    # Homeowner Phone Number
    def get_homeowner_phone_number(self) -> Optional[str]:
        """
        Get phone number of homeowner.

        Returns:
            str: Phone number or None if not set
        """
        return self.homeowner_phone_number

    def set_homeowner_phone_number(self, phone_number: str) -> bool:
        """
        Set phone number of homeowner.

        Args:
            phone_number (str): Phone number to set

        Returns:
            bool: True if successful, False otherwise
        """
        if not isinstance(phone_number, str):
            return False
        self.homeowner_phone_number = phone_number
        return True

    # System Lock Time
    def get_system_lock_time(self) -> Optional[int]:
        """
        Get system lock time in minutes.

        Returns:
            int: Lock time in minutes or None if not set
        """
        return self.system_lock_time

    def set_system_lock_time(self, lock_time: int) -> bool:
        """
        Set system lock time.

        Args:
            lock_time (int): Lock time in minutes

        Returns:
            bool: True if successful, False otherwise
        """
        if not isinstance(lock_time, int) or lock_time < 0:
            return False
        self.system_lock_time = lock_time
        return True

    # Alarm Delay Time
    def get_alarm_delay_time(self) -> Optional[int]:
        """
        Get delay time before alarming in minutes.

        Returns:
            int: Delay time in minutes or None if not set
        """
        return self.alarm_delay_time

    def set_alarm_delay_time(self, delay_time: int) -> bool:
        """
        Set delay time before alarming.

        Args:
            delay_time (int): Delay time in minutes

        Returns:
            bool: True if successful, False otherwise
        """
        if not isinstance(delay_time, int):
            return False
        if delay_time < 5:
            raise ValueError("Alarm delay time must be at least 5 minutes")
        self.alarm_delay_time = delay_time
        return True

    def __str__(self) -> str:
        """String representation of SystemSettings."""
        return (
            f"SystemSettings("
            f"panic_phone_number='{self.panic_phone_number}', "
            f"homeowner_phone_number='{self.homeowner_phone_number}', "
            f"lock_time={self.system_lock_time}min, "
            f"alarm_delay={self.alarm_delay_time}min)"
        )

    def to_schema(self) -> SystemSettingSchema:
        """Convert SystemSettings to SystemSettingSchema."""
        return SystemSettingSchema(
            system_setting_id=self.system_setting_id,
            panic_phone_number=self.panic_phone_number,
            homeowner_phone_number=self.homeowner_phone_number,
            system_lock_time=self.system_lock_time,
            alarm_delay_time=self.alarm_delay_time,
        )
