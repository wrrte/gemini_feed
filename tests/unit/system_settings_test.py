from datetime import datetime

import pytest

from configurations.system_settings import SystemSettings


def test_system_settings_initialization_all_params():
    """Test SystemSettings initialization with all parameters"""
    now = datetime.now()
    settings = SystemSettings(
        system_setting_id=1,
        panic_phone_number="911",
        homeowner_phone_number="555-1234",
        system_lock_time=30,
        alarm_delay_time=10,
        created_at=now,
        updated_at=now,
    )

    assert settings.system_setting_id == 1
    assert settings.get_panic_phone_number() == "911"
    assert settings.get_homeowner_phone_number() == "555-1234"
    assert settings.get_system_lock_time() == 30
    assert settings.get_alarm_delay_time() == 10


def test_system_settings_initialization_defaults():
    """Test SystemSettings initialization with default None values"""
    settings = SystemSettings(system_setting_id=1)

    assert settings.system_setting_id == 1
    assert settings.get_panic_phone_number() is None
    assert settings.get_homeowner_phone_number() is None
    assert settings.get_system_lock_time() is None
    assert settings.get_alarm_delay_time() is None


def test_system_settings_set_panic_phone_number():
    """Test setting panic phone number with valid string"""
    settings = SystemSettings(system_setting_id=1)

    result = settings.set_panic_phone_number("911")
    assert result is True
    assert settings.get_panic_phone_number() == "911"


def test_system_settings_set_panic_phone_number_invalid_type():
    """Test setting panic phone number with invalid type"""
    settings = SystemSettings(system_setting_id=1, panic_phone_number="911")

    result = settings.set_panic_phone_number(12345)
    assert result is False
    assert (
        settings.get_panic_phone_number() == "911"
    )  # Should remain unchanged


def test_system_settings_get_panic_phone_number():
    """Test getting panic phone number"""
    settings = SystemSettings(system_setting_id=1, panic_phone_number="112")

    assert settings.get_panic_phone_number() == "112"


def test_system_settings_get_panic_phone_number_none():
    """Test getting panic phone number when None"""
    settings = SystemSettings(system_setting_id=1)

    assert settings.get_panic_phone_number() is None


def test_system_settings_set_homeowner_phone_number():
    """Test setting homeowner phone number with valid string"""
    settings = SystemSettings(system_setting_id=1)

    result = settings.set_homeowner_phone_number("555-1234")
    assert result is True
    assert settings.get_homeowner_phone_number() == "555-1234"


def test_system_settings_set_homeowner_phone_number_invalid_type():
    """Test setting homeowner phone number with invalid type"""
    settings = SystemSettings(
        system_setting_id=1, homeowner_phone_number="555-0000"
    )

    result = settings.set_homeowner_phone_number(5551234)
    assert result is False
    assert settings.get_homeowner_phone_number() == "555-0000"


def test_system_settings_get_homeowner_phone_number():
    """Test getting homeowner phone number"""
    settings = SystemSettings(
        system_setting_id=1, homeowner_phone_number="555-9876"
    )

    assert settings.get_homeowner_phone_number() == "555-9876"


def test_system_settings_get_homeowner_phone_number_none():
    """Test getting homeowner phone number when None"""
    settings = SystemSettings(system_setting_id=1)

    assert settings.get_homeowner_phone_number() is None


def test_system_settings_set_system_lock_time():
    """Test setting system lock time with valid integer"""
    settings = SystemSettings(system_setting_id=1)

    result = settings.set_system_lock_time(45)
    assert result is True
    assert settings.get_system_lock_time() == 45


def test_system_settings_set_system_lock_time_zero():
    """Test setting system lock time with zero"""
    settings = SystemSettings(system_setting_id=1)

    result = settings.set_system_lock_time(0)
    assert result is True
    assert settings.get_system_lock_time() == 0


def test_system_settings_set_system_lock_time_negative():
    """Test setting system lock time with negative value"""
    settings = SystemSettings(system_setting_id=1, system_lock_time=30)

    result = settings.set_system_lock_time(-5)
    assert result is False
    assert settings.get_system_lock_time() == 30  # Should remain unchanged


def test_system_settings_set_system_lock_time_invalid_type():
    """Test setting system lock time with invalid type"""
    settings = SystemSettings(system_setting_id=1, system_lock_time=30)

    result = settings.set_system_lock_time("30")
    assert result is False
    assert settings.get_system_lock_time() == 30


def test_system_settings_get_system_lock_time():
    """Test getting system lock time"""
    settings = SystemSettings(system_setting_id=1, system_lock_time=60)

    assert settings.get_system_lock_time() == 60


def test_system_settings_get_system_lock_time_none():
    """Test getting system lock time when None"""
    settings = SystemSettings(system_setting_id=1)

    assert settings.get_system_lock_time() is None


def test_system_settings_set_alarm_delay_time():
    """Test setting alarm delay time with valid value"""
    settings = SystemSettings(system_setting_id=1)

    result = settings.set_alarm_delay_time(10)
    assert result is True
    assert settings.get_alarm_delay_time() == 10


def test_system_settings_set_alarm_delay_time_minimum():
    """Test setting alarm delay time with minimum value (5 minutes)"""
    settings = SystemSettings(system_setting_id=1)

    result = settings.set_alarm_delay_time(5)
    assert result is True
    assert settings.get_alarm_delay_time() == 5


def test_system_settings_set_alarm_delay_time_below_minimum():
    """Test setting alarm delay time below minimum raises ValueError"""
    settings = SystemSettings(system_setting_id=1, alarm_delay_time=10)

    with pytest.raises(
        ValueError, match="Alarm delay time must be at least 5 minutes"
    ):
        settings.set_alarm_delay_time(4)

    # Value should remain unchanged
    assert settings.get_alarm_delay_time() == 10


def test_system_settings_set_alarm_delay_time_invalid_type():
    """Test setting alarm delay time with invalid type"""
    settings = SystemSettings(system_setting_id=1, alarm_delay_time=10)

    result = settings.set_alarm_delay_time("10")
    assert result is False
    assert settings.get_alarm_delay_time() == 10


def test_system_settings_get_alarm_delay_time():
    """Test getting alarm delay time"""
    settings = SystemSettings(system_setting_id=1, alarm_delay_time=15)

    assert settings.get_alarm_delay_time() == 15


def test_system_settings_get_alarm_delay_time_none():
    """Test getting alarm delay time when None"""
    settings = SystemSettings(system_setting_id=1)

    assert settings.get_alarm_delay_time() is None


def test_system_settings_str():
    """Test string representation"""
    settings = SystemSettings(
        system_setting_id=1,
        panic_phone_number="911",
        homeowner_phone_number="555-1234",
        system_lock_time=30,
        alarm_delay_time=10,
    )

    str_repr = str(settings)
    assert "panic_phone_number='911'" in str_repr
    assert "homeowner_phone_number='555-1234'" in str_repr
    assert "lock_time=30min" in str_repr
    assert "alarm_delay=10min" in str_repr


def test_system_settings_str_with_none_values():
    """Test string representation with None values"""
    settings = SystemSettings(system_setting_id=1)

    str_repr = str(settings)
    assert "panic_phone_number='None'" in str_repr
    assert "homeowner_phone_number='None'" in str_repr
    assert "lock_time=Nonemin" in str_repr
    assert "alarm_delay=Nonemin" in str_repr


def test_system_settings_to_schema():
    """Test conversion to SystemSettingSchema"""
    settings = SystemSettings(
        system_setting_id=1,
        panic_phone_number="911",
        homeowner_phone_number="555-1234",
        system_lock_time=30,
        alarm_delay_time=10,
    )

    schema = settings.to_schema()

    assert schema.system_setting_id == 1
    assert schema.panic_phone_number == "911"
    assert schema.homeowner_phone_number == "555-1234"
    assert schema.system_lock_time == 30
    assert schema.alarm_delay_time == 10


def test_system_settings_to_schema_with_none_values():
    """Test conversion to schema with None values"""
    settings = SystemSettings(system_setting_id=2)

    schema = settings.to_schema()

    assert schema.system_setting_id == 2
    assert schema.panic_phone_number is None
    assert schema.homeowner_phone_number is None
    assert schema.system_lock_time is None
    assert schema.alarm_delay_time is None


def test_system_settings_set_alarm_delay_time_zero():
    """Test setting alarm delay time with zero raises ValueError"""
    settings = SystemSettings(system_setting_id=1, alarm_delay_time=10)

    with pytest.raises(
        ValueError, match="Alarm delay time must be at least 5 minutes"
    ):
        settings.set_alarm_delay_time(0)

    assert settings.get_alarm_delay_time() == 10


def test_system_settings_set_alarm_delay_time_negative():
    """Test setting alarm delay time with negative value raises ValueError"""
    settings = SystemSettings(system_setting_id=1, alarm_delay_time=10)

    with pytest.raises(
        ValueError, match="Alarm delay time must be at least 5 minutes"
    ):
        settings.set_alarm_delay_time(-5)

    assert settings.get_alarm_delay_time() == 10
