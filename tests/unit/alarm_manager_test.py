from unittest.mock import Mock

import pytest

from device.appliance.interface_alarm import InterfaceAlarm
from manager.alarm_manager import AlarmManager


@pytest.fixture
def mock_alarm_interface():
    return Mock(spec=InterfaceAlarm)


@pytest.fixture
def alarm_manager(mock_alarm_interface):
    return AlarmManager(alarm=mock_alarm_interface)


def test_init(alarm_manager, mock_alarm_interface):
    assert alarm_manager.alarm == mock_alarm_interface


def test_ring_alarm(alarm_manager, mock_alarm_interface):
    alarm_manager.ring_alarm()
    mock_alarm_interface.ring_alarm.assert_called_once()


def test_stop_alarm(alarm_manager, mock_alarm_interface):
    alarm_manager.stop_alarm()
    mock_alarm_interface.stop_alarm.assert_called_once()


def test_is_ringing(alarm_manager, mock_alarm_interface):
    mock_alarm_interface.is_ringing.return_value = True
    assert alarm_manager.is_ringing() is True

    mock_alarm_interface.is_ringing.return_value = False
    assert alarm_manager.is_ringing() is False
