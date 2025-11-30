from device.appliance.interface_alarm import InterfaceAlarm


class AlarmManager:
    """
    AlarmManager class to manage alarms.
    """

    def __init__(self, alarm: InterfaceAlarm):
        """
        Initialize the AlarmManager.
        """
        self.alarm = alarm

    def ring_alarm(self):
        """
        Ring the alarm.
        """
        self.alarm.ring_alarm()

    def stop_alarm(self):
        """
        Stop the alarm.
        """
        self.alarm.stop_alarm()

    def is_ringing(self):
        """
        Check if the alarm is ringing.
        """
        return self.alarm.is_ringing()
