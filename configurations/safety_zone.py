from datetime import datetime


class SafetyZone:
    """
    Manages the information for each SafetyZone such as
    the SafetyZone ID, name, sensors list of SafetyZone,
    the armed status of SafetyZone.
    """

    def __init__(
        self,
        zone_id: int,
        zone_name: str,
        coordinate_x1: float,
        coordinate_y1: float,
        coordinate_x2: float,
        coordinate_y2: float,
        sensor_id_list: list[int] = [],
        arm_status: bool = False,
        updated_at: datetime = None,
        created_at: datetime = None,
    ):
        self.zone_id = zone_id
        self.zone_name = zone_name
        self.coordinate_x1 = coordinate_x1
        self.coordinate_y1 = coordinate_y1
        self.coordinate_x2 = coordinate_x2
        self.coordinate_y2 = coordinate_y2
        self.sensor_id_list = sensor_id_list.copy() if sensor_id_list else []
        self.arm_status = arm_status
        self.updated_at = updated_at
        self.created_at = created_at

    def set_id(self, zone_id):
        """
        Set the SafetyZone ID.

        Args:
            zone_id (int): The unique identifier for the safety zone

        Returns:
            bool: True if successful, False otherwise
        """
        if not isinstance(zone_id, int):
            return False
        self.zone_id = zone_id
        return True

    def get_zone_id(self):
        """
        Get the SafetyZone ID.

        Returns:
            int: The SafetyZone ID
        """
        return self.zone_id

    def set_zone_name(self, zone_name):
        """
        Set the SafetyZone name.

        Args:
            zone_name (str): The name of the safety zone

        Returns:
            bool: True if successful, False otherwise
        """
        if not isinstance(zone_name, str):
            return False
        self.zone_name = zone_name
        return True

    def get_zone_name(self):
        """
        Get the SafetyZone name.

        Returns:
            str: The SafetyZone name
        """
        return self.zone_name

    def set_coordinates(self, x1, y1, x2, y2):
        """
        Set the coordinates defining the rectangular zone boundaries.

        Args:
            x1 (float/int): X coordinate of first corner
            y1 (float/int): Y coordinate of first corner
            x2 (float/int): X coordinate of opposite corner
            y2 (float/int): Y coordinate of opposite corner

        Returns:
            bool: True if all 4 coordinates are successfully set,
            False otherwise.
            If any coordinate is invalid, none are saved.
        """
        # Validate all coordinates before saving any
        if not all(
            isinstance(coord, (int, float)) for coord in [x1, y1, x2, y2]
        ):
            return False

        # All valid - save as tuple
        self.coordinate_x1 = x1
        self.coordinate_y1 = y1
        self.coordinate_x2 = x2
        self.coordinate_y2 = y2
        return True

    def get_coordinates(self) -> tuple[float, float, float, float]:
        """
        Get the coordinates defining the rectangular zone boundaries.

        Returns:
            tuple: (x1, y1, x2, y2) or None if not set
        """
        return (
            self.coordinate_x1,
            self.coordinate_y1,
            self.coordinate_x2,
            self.coordinate_y2,
        )

    def set_sensor_list(self, sensor_ids: list[int]) -> bool:
        """
        Set the sensors list for this SafetyZone.

        Args:
            sensor_ids (list[int]): List of sensor IDs to assign to this zone

        Returns:
            bool: True if successful, False otherwise
        """
        if not isinstance(sensor_ids, list):
            return False
        if not all(isinstance(sensor_id, int) for sensor_id in sensor_ids):
            return False
        self.sensor_id_list = sensor_ids.copy()
        return True

    def get_sensor_list(self):
        """
        Get the sensors list of this SafetyZone.

        Returns:
            list[int]: List of sensor IDs in this zone
        """
        return self.sensor_id_list.copy()

    def add_sensor(self, sensor_id):
        """
        Add a single sensor to this SafetyZone.

        Args:
            sensor_id (int): The sensor ID to add

        Returns:
            bool: True if successful, False if sensor already exists
        """
        if sensor_id not in self.sensor_id_list and isinstance(sensor_id, int):
            self.sensor_id_list.append(sensor_id)
            return True
        return False

    def remove_sensor(self, sensor_id):
        """
        Remove a single sensor from this SafetyZone.

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
        Remove all sensors from this SafetyZone.
        """
        self.sensor_id_list.clear()

    def is_armed(self):
        """
        Check if the SafetyZone is armed.

        Returns:
            bool: True if armed, False otherwise
        """
        return self.arm_status

    def arm(self):
        """
        Arm the SafetyZone.
        """
        self.arm_status = True

    def disarm(self):
        """
        Disarm the SafetyZone.
        """
        self.arm_status = False

    def to_schema(self):
        """
        Convert SafetyZone to SafetyZoneSchema.

        Returns:
            SafetyZoneSchema: Schema representation of this SafetyZone
        """
        from database.schema.safety_zone import SafetyZoneSchema

        return SafetyZoneSchema(
            zone_id=self.zone_id,
            zone_name=self.zone_name,
            coordinate_x1=self.coordinate_x1,
            coordinate_y1=self.coordinate_y1,
            coordinate_x2=self.coordinate_x2,
            coordinate_y2=self.coordinate_y2,
            arm_status=self.arm_status,
            sensor_id_list=self.sensor_id_list,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def __str__(self):
        """String representation of SafetyZone."""
        status = "ARMED" if self.arm_status else "DISARMED"
        return (
            f"SafetyZone(ID={self.zone_id}, "
            f"Name='{self.zone_name}', "
            f"Sensors={len(self.sensor_id_list)}, "
            f"Status={status})"
        )
