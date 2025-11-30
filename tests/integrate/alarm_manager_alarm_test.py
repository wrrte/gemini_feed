"""
Integration Test: AlarmManager + Alarm

Tests the interaction between AlarmManager and actual Alarm device.
Verifies ring/stop operations and alarm state management.
"""

import time

import pytest

from device.appliance.alarm import Alarm
from manager.alarm_manager import AlarmManager

# ==================== Fixtures ====================


@pytest.fixture
def alarm():
    """Create a real Alarm instance."""
    alarm_instance = Alarm()
    alarm_instance.set_id(1)
    yield alarm_instance
    # Cleanup: shutdown alarm thread
    alarm_instance.shutdown()


@pytest.fixture
def alarm_manager(alarm):
    """Create AlarmManager with real Alarm instance."""
    return AlarmManager(alarm=alarm)


# ==================== Ring/Stop Integration Tests ====================


def test_alarm_manager_ring_alarm(alarm_manager, alarm):
    """Test ringing alarm through manager."""
    # Act
    alarm_manager.ring_alarm()

    # Assert
    assert alarm_manager.is_ringing() is True
    assert alarm.is_ringing() is True

    # Cleanup
    alarm_manager.stop_alarm()


def test_alarm_manager_stop_alarm(alarm_manager, alarm):
    """Test stopping alarm through manager."""
    # Arrange
    alarm_manager.ring_alarm()

    # Act
    alarm_manager.stop_alarm()

    # Assert
    assert alarm_manager.is_ringing() is False
    assert alarm.is_ringing() is False


def test_alarm_manager_stop_already_stopped_alarm(alarm_manager, alarm):
    """Test stopping an already stopped alarm (no error)."""
    # Arrange - alarm is not ringing

    # Act
    alarm_manager.stop_alarm()

    # Assert
    assert alarm_manager.is_ringing() is False
    assert alarm.is_ringing() is False


def test_alarm_manager_ring_already_ringing_alarm(alarm_manager, alarm):
    """Test ringing an already ringing alarm (idempotent)."""
    # Arrange
    alarm_manager.ring_alarm()
    initial_start_time = alarm.ring_start_time

    # Small delay to ensure time difference if start_time changes
    time.sleep(0.01)

    # Act
    alarm_manager.ring_alarm()

    # Assert - should still be ringing, start time unchanged
    assert alarm_manager.is_ringing() is True
    assert alarm.ring_start_time == initial_start_time

    # Cleanup
    alarm_manager.stop_alarm()


def test_alarm_manager_is_ringing_reflects_alarm_state(alarm_manager, alarm):
    """Test that manager's is_ringing reflects actual alarm state."""
    # Initially not ringing
    assert alarm_manager.is_ringing() is False

    # Ring alarm directly
    alarm.ring_alarm()
    assert alarm_manager.is_ringing() is True

    # Stop alarm directly
    alarm.stop_alarm()
    assert alarm_manager.is_ringing() is False


# ==================== State Management Tests ====================


def test_alarm_state_after_ring_and_stop_cycle(alarm_manager, alarm):
    """Test complete ring-stop cycle."""
    # Initial state
    assert alarm_manager.is_ringing() is False

    # Ring
    alarm_manager.ring_alarm()
    assert alarm_manager.is_ringing() is True

    # Stop
    alarm_manager.stop_alarm()
    assert alarm_manager.is_ringing() is False


def test_alarm_ring_start_time_set(alarm_manager, alarm):
    """Test that ring_start_time is set when alarm rings."""
    # Arrange
    assert alarm.ring_start_time is None

    # Act
    alarm_manager.ring_alarm()

    # Assert
    assert alarm.ring_start_time is not None

    # Cleanup
    alarm_manager.stop_alarm()


def test_alarm_ring_start_time_cleared_on_stop(alarm_manager, alarm):
    """Test that ring_start_time is cleared when alarm stops."""
    # Arrange
    alarm_manager.ring_alarm()
    assert alarm.ring_start_time is not None

    # Act
    alarm_manager.stop_alarm()

    # Assert
    assert alarm.ring_start_time is None


# ==================== Alarm Device Direct Tests ====================


def test_alarm_set_id(alarm):
    """Test setting alarm ID."""
    # Act
    result = alarm.set_id(42)

    # Assert
    assert result is True
    assert alarm.get_id() == 42


def test_alarm_set_id_invalid_type(alarm):
    """Test setting alarm ID with invalid type."""
    # Act
    result = alarm.set_id("invalid")

    # Assert
    assert result is False


def test_alarm_get_location(alarm):
    """Test getting alarm location."""
    # Act
    location = alarm.get_location()

    # Assert
    assert location == (0, 0)  # Default location


def test_alarm_get_info_silent(alarm):
    """Test getting alarm info when silent."""
    # Act
    info = alarm.get_info()

    # Assert
    assert info["alarm_id"] == 1
    assert info["status"] == "SILENT"
    assert info["ringing"] is False


def test_alarm_get_info_ringing(alarm):
    """Test getting alarm info when ringing."""
    # Arrange
    alarm.ring_alarm()

    # Act
    info = alarm.get_info()

    # Assert
    assert info["status"] == "RINGING"
    assert info["ringing"] is True

    # Cleanup
    alarm.stop_alarm()


# ==================== Thread Safety Tests ====================


def test_alarm_concurrent_ring_stop(alarm_manager, alarm):
    """Test rapid ring/stop operations for thread safety."""
    # Act - rapid operations
    for _ in range(10):
        alarm_manager.ring_alarm()
        alarm_manager.stop_alarm()

    # Assert - should end in stopped state
    assert alarm_manager.is_ringing() is False


def test_alarm_manager_with_alarm_thread_running(alarm):
    """Test that AlarmManager works with alarm's background thread."""
    # Arrange - alarm thread is running
    manager = AlarmManager(alarm=alarm)

    # Act
    manager.ring_alarm()
    time.sleep(0.05)  # Let thread process

    # Assert
    assert manager.is_ringing() is True

    # Cleanup
    manager.stop_alarm()


# ==================== Edge Cases ====================


def test_multiple_alarm_managers_same_alarm(alarm):
    """Test multiple managers controlling same alarm."""
    # Arrange
    manager1 = AlarmManager(alarm=alarm)
    manager2 = AlarmManager(alarm=alarm)

    # Act - manager1 rings
    manager1.ring_alarm()

    # Assert - both see ringing state
    assert manager1.is_ringing() is True
    assert manager2.is_ringing() is True

    # Act - manager2 stops
    manager2.stop_alarm()

    # Assert - both see stopped state
    assert manager1.is_ringing() is False
    assert manager2.is_ringing() is False
