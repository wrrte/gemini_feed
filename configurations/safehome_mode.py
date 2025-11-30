from datetime import datetime
from typing import Optional

from database.schema.safehome_mode import SafeHomeModeSchema


class SafeHomeMode:
    """
    Manages the sensor list for each SafeHome Mode such as
    Home, Away, Overnight travel, Extended Travel.
    """

    def __init__(
        self,
        mode_id: int,
        mode_name: str,
        sensor_ids: list[int],
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """
        Initialize a SafeHomeMode.

        Args:
            mode_id: int
            mode_name: str
            sensor_ids: list[int]
            created_at: Optional[datetime] = None
            updated_at: Optional[datetime] = None
        """
        self.mode_id = mode_id
        self.mode_name = mode_name
        self.sensor_id_list = sensor_ids.copy() if sensor_ids else []
        self.created_at = created_at
        self.updated_at = updated_at

    def set_id(self, mode_id):
        """
        Set the SafeHomeMode ID.

        Args:
            mode_id (int): The unique identifier for the mode

        Returns:
            bool: True if successful, False otherwise
        """
        if not isinstance(mode_id, int):
            return False
        self.mode_id = mode_id
        return True

    def get_id(self):
        """
        Get the SafeHomeMode ID.

        Returns:
            int: The SafeHomeMode ID
        """
        return self.mode_id

    def get_mode_name(self):
        """
        Get the mode name.

        Returns:
            str: The mode name
        """
        return self.mode_name

    def set_sensor_list(self, sensor_ids: list[int]):
        """
        Set the sensors list for this SafeHomeMode.

        Args:
            sensor_ids (list[int]): List of sensor IDs to assign to this mode

        Returns:
            bool: True if successful, False otherwise
        """
        self.sensor_id_list = sensor_ids.copy()
        return True

    def get_sensor_list(self):
        """
        Get the sensors list of this SafeHomeMode.

        Returns:
            list[int]: List of sensor IDs in this mode
        """
        return self.sensor_id_list.copy()

    def add_sensor(self, sensor_id: int):
        """
        Add a sensor to this SafeHomeMode.

        Args:
            sensor_id (int): The sensor ID to add

        Returns:
            bool: True if successful, False if sensor already exists
        """
        if sensor_id not in self.sensor_id_list and isinstance(sensor_id, int):
            self.sensor_id_list.append(sensor_id)
            return True
        return False

    def remove_sensor(self, sensor_id: int):
        """
        Remove a sensor from this SafeHomeMode.

        Args:
            sensor_id (int): The sensor ID to remove

        Returns:
            bool: True if successful, False if sensor not found
        """
        if sensor_id in self.sensor_id_list:
            self.sensor_id_list.remove(sensor_id)
            return True
        return False

    def delete_all_sensors(self):
        """
        Remove all sensors from this SafeHomeMode.
        """
        self.sensor_id_list.clear()
        self.appliance_id_list.clear()

    def __str__(self):
        """String representation of SafeHomeMode."""
        return (
            f"SafeHomeMode(ID={self.mode_id}, Mode='{self.mode_name}', "
            f"Sensors={len(self.sensor_id_list)},"
            f"Appliances={len(self.appliance_id_list)})"
        )

    def to_schema(self) -> SafeHomeModeSchema:
        """
        Convert SafeHomeMode to schema.

        Returns:
            SafeHomeModeSchema: The schema representation of SafeHomeMode
        """
        return SafeHomeModeSchema(
            mode_id=self.mode_id,
            mode_name=self.mode_name,
            sensor_ids=self.sensor_id_list,
            created_at=self.created_at,
        )
