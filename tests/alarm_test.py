
from unittest.mock import patch

import pytest

from device.appliance.alarm import ALARM_DURATION, Alarm


@pytest.fixture
def mock_thread_start():
    """Prevent the thread from actually starting during __init__."""
    with patch("threading.Thread.start") as mock_start:
        yield mock_start


@pytest.fixture
def alarm(mock_thread_start):
    return Alarm()


def test_init_success(alarm, mock_thread_start):
    assert alarm.alarm_id == 0
    assert alarm.ringing is False
    assert alarm._running is True
    # Verify thread start was called
    mock_thread_start.assert_called_once()


def test_set_id_success(alarm):
    result = alarm.set_id(5)
    assert result is True
    assert alarm.get_id() == 5


def test_set_id_invalid_type(alarm):
    result = alarm.set_id("invalid")
    assert result is False
    assert alarm.get_id() == 0


def test_get_location(alarm):
    assert alarm.get_location() == (0, 0)


def test_ring_alarm_start(alarm):
    with patch("time.time", return_value=1000.0):
        alarm.ring_alarm()

    assert alarm.is_ringing() is True
    assert alarm.ring_start_time == 1000.0


def test_ring_alarm_already_ringing(alarm):
    alarm.ringing = True
    alarm.ring_start_time = 1000.0

    alarm.ring_alarm()

    # Should not print "ringing started" again if logic checks ringing state
    # (The implementation prints only if not self.ringing)
    assert alarm.is_ringing() is True


def test_stop_alarm_success(alarm):
    alarm.ring_alarm()
    assert alarm.is_ringing() is True

    alarm.stop_alarm()
    assert alarm.is_ringing() is False
    assert alarm.ring_start_time is None


def test_stop_alarm_when_not_ringing(alarm):
    alarm.ringing = False
    alarm.stop_alarm()
    assert alarm.is_ringing() is False


def test_get_info_ringing(alarm):
    alarm.ringing = True
    alarm.alarm_id = 1
    info = alarm.get_info()

    assert info["alarm_id"] == 1
    assert info["status"] == "RINGING"
    assert info["ringing"] is True


def test_get_info_silent(alarm):
    alarm.ringing = False
    info = alarm.get_info()
    assert info["status"] == "SILENT"


def test_shutdown(alarm):
    alarm.ringing = True
    alarm.shutdown()

    assert alarm._running is False
    assert alarm.ringing is False


@patch("time.sleep")
@patch("time.time")
def test_run_loop_auto_stop(mock_time, mock_sleep, alarm):
    """
    Test the run loop auto-stop logic.
    We simulate the loop running once by having side_effect on sleep.
    """
    # Setup: Alarm is ringing, time has passed ALARM_DURATION
    alarm.ringing = True
    start_t = 1000.0
    alarm.ring_start_time = start_t

    # Sequence of time.time calls:
    # 1. Inside loop check: current time > start + duration
    # 2. Inside stop_alarm calculation
    # 3. Inside stop_alarm calculation (if needed)
    current_t = start_t + ALARM_DURATION + 10
    mock_time.return_value = current_t

    # Side effect for sleep to break the loop after one iteration
    def stop_loop(*args):
        alarm._running = False

    mock_sleep.side_effect = stop_loop

    alarm.run()

    assert alarm.ringing is False
    mock_sleep.assert_called()


@patch("time.sleep")
@patch("time.time")
def test_run_loop_no_auto_stop(mock_time, mock_sleep, alarm):
    """Test run loop when duration hasn't passed."""
    alarm.ringing = True
    start_t = 1000.0
    alarm.ring_start_time = start_t

    # Time has not passed duration yet
    mock_time.return_value = start_t + 1

    def stop_loop(*args):
        alarm._running = False
    mock_sleep.side_effect = stop_loop

    alarm.run()

    assert alarm.ringing is True
