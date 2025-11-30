from typing import Optional

from configurations.safehome_mode import SafeHomeMode
from configurations.safety_zone import SafetyZone
from configurations.system_settings import SystemSettings
from database.schema.safehome_mode import SafeHomeModeSchema
from database.schema.safety_zone import SafetyZoneSchema
from database.schema.sensor import SensorType
from database.schema.system_setting import SystemSettingSchema
from manager.sensor_manager import SensorManager
from manager.storage_manager import StorageManager

"""
ConfigurationManager - Manages system configuration including
SafeHomeMode, SafetyZone, and SystemSettings.
"""


class ConfigurationManager:
    """
    Manage the access to configuration of the SafeHome system which includes
    System settings, Safety Zone information, SafeHome mode information.
    """

    # ====================Initialization====================
    def __init__(
        self,
        storage_manager: Optional[StorageManager] = None,
        sensor_manager: Optional[SensorManager] = None,
    ):
        """
        Initialize the ConfigurationManager.
        """
        self.system_settings: SystemSettings = None
        self.safehome_modes: dict[int, SafeHomeMode] = {}
        self.safety_zones: dict[int, SafetyZone] = {}
        self.storage_manager: StorageManager = storage_manager
        self.sensor_manager: SensorManager = sensor_manager

        # init configuration manager
        self._init_configuration_manager()

    def _init_configuration_manager(self) -> None:
        """
        Initialize the configuration information by loading from database
        and creating default configurations if needed.
        """
        # Initialize SystemSettings and load from database
        self._load_system_settings()

        # Load SafeHome modes from database
        self._load_safehome_modes()

        # Load Safety zones from database
        self._load_safety_zones()

    def clean_up_configuration_manager(self) -> None:
        """
        Clean up the configuration manager.
        - save configurations to database
        - other clean up operations
        """
        # TODO: Implement this
        pass

    def save_configurations(self) -> None:
        """
        Save the configurations to the database.
        - save current system settings
        - save current safehome modes
        - save current safety zones
        """
        # TODO: Implement this
        pass

    def _load_safehome_modes(self) -> None:
        """
        Load SafeHome modes from database.
        Creates default modes with empty sensor/appliance lists if none exist.
        """
        # Load modes from safehome_modes table
        schemas = self.storage_manager.get_all_safehome_modes()

        for schema in schemas:
            mode = SafeHomeMode(**schema.model_dump())
            self.safehome_modes[mode.mode_id] = mode

    def _load_system_settings(self) -> None:
        """
        Load system settings from database into SystemSettings object.
        """
        try:
            # Load system settings from database
            schema = self.storage_manager.get_system_setting(1)
            if schema:
                self.system_settings = SystemSettings(**schema.model_dump())
            else:
                raise ValueError("System settings not found")

        except Exception as e:
            print(f"Error loading system settings from database: {e}")

    def _load_safety_zones(self) -> None:
        """
        Load Safety zones from database.
        """
        # Load zones from safety_zones table
        zones = self.storage_manager.get_all_safety_zones()
        self.safety_zones = {
            zone.zone_id: SafetyZone(
                zone.zone_id,
                zone.zone_name,
                zone.coordinate_x1,
                zone.coordinate_y1,
                zone.coordinate_x2,
                zone.coordinate_y2,
                arm_status=zone.arm_status,
            )
            for zone in zones
        }

    # ==================== System settings ====================

    def get_system_setting(self) -> Optional[SystemSettings]:
        """
        Get system setting information.

        Returns:
            SystemSettings: The current system settings
            or None if not initialized
        """
        return self.system_settings

    def update_system_setting(self, schema: SystemSettingSchema) -> bool:
        """
        Update system setting information.

        Args:
            schema: System setting schema
        """
        try:
            # Update database using unified method
            if not self.storage_manager.update_system_setting(schema):
                print(
                    f"Failed to update system setting\
                    with id {schema.system_setting_id}"
                )
                return False

            # Update cache
            self.system_settings = SystemSettings(**schema.model_dump())
            return True
        except Exception as e:
            print(f"Failed to update system setting: {e}")
            return False

    # ==================== SafeHome Modes ====================

    def get_safehome_mode(self, id: int) -> Optional[SafeHomeMode]:
        """
        Get SafeHome mode by ID.

        Args:
            id (int): The mode ID to retrieve

        Returns:
            SafeHomeMode: The SafeHomeMode object or None if not found
        """
        if not isinstance(id, int):
            return None

        return self.safehome_modes.get(id)

    def get_safehome_mode_by_name(self, name: str) -> Optional[SafeHomeMode]:
        """
        Get SafeHome mode by name.
        """
        mode_dict = self.get_all_safehome_modes()
        for mode in mode_dict.values():
            if mode.mode_name == name:
                return mode
        return None

    def get_all_safehome_modes(self) -> dict[int, SafeHomeMode]:
        """
        Get all SafeHome modes.

        Returns:
            dict[int, SafeHomeMode]: Dictionary of all SafeHome modes
        """
        return self.safehome_modes

    def update_safehome_mode(self, schema: SafeHomeModeSchema) -> bool:
        """
        Update a SafeHome mode configuration.

        Args:
            schema: SafeHomeModeSchema

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # check if mode exists
            if schema.mode_id not in self.safehome_modes:
                print(f"SafeHome mode with id {schema.mode_id} not found")
                return False

            # update database
            if not self.storage_manager.update_safehome_mode(schema):
                print(f"Failed to update safehome mode {schema.mode_id}")
                return False

            # Update cache
            self.safehome_modes[schema.mode_id] = SafeHomeMode(
                **schema.model_dump()
            )

            return True
        except Exception as e:
            print(f"Failed to update safehome mode {schema.mode_id}: {e}")
            return False

    def change_to_safehome_mode(self, mode_name: str) -> bool:
        """
        Change to a SafeHome mode.
        update related sensors to the mode

        Returns:
            bool: True if successful, False otherwise
        """
        # check if mode exists
        mode = self.get_safehome_mode_by_name(mode_name)
        if not mode:
            print(f"SafeHome mode with name {mode_name} not found")
            return False

        # update(arm/disarm) related sensors to the mode
        to_be_armed_sensors = mode.get_sensor_list()
        for sensor_id in self.sensor_manager.sensor_dict.keys():
            if sensor_id in to_be_armed_sensors:
                self.sensor_manager.arm_sensor(sensor_id)
            else:
                self.sensor_manager.disarm_sensor(sensor_id)

        return True

    # ==================== Safety Zones ====================

    def get_safety_zone(self, id: int) -> Optional[SafetyZone]:
        """
        Get Safety Zone by ID.

        Args:
            id (int): The zone ID to retrieve

        Returns:
            SafetyZone: The SafetyZone object or None if not found
        """
        if not isinstance(id, int):
            return None

        return self.safety_zones.get(id)

    def get_all_safety_zones(self) -> dict[int, SafetyZone]:
        """
        Get all Safety zones.

        Returns:
            dict[int, SafetyZone]: Dictionary of all Safety zones
        """
        return self.safety_zones

    def update_safety_zone(
        self,
        schema: SafetyZoneSchema,
    ) -> bool:
        """
        Update a safety zone configuration.
        """
        if not isinstance(schema.zone_id, int):
            return False

        # Check if zone exists
        if schema.zone_id not in self.safety_zones:
            print(f"Safety zone with id {schema.zone_id} not found")
            return False

        try:
            # Update database using unified method
            if not self.storage_manager.update_safety_zone(schema):
                print(f"Failed to update safety zone {schema.zone_id}")
                return False

            # Load updated zone from database
            updated_zone = self.storage_manager.get_safety_zone(schema.zone_id)
            if not updated_zone:
                print(f"Failed to load updated safety zone {schema.zone_id}")
                return False

            # Update cache
            self.safety_zones[schema.zone_id] = SafetyZone(
                **updated_zone.model_dump()
            )

            return True
        except Exception as e:
            print(f"Failed to update safety zone {schema.zone_id}: {e}")
            return False

    def add_safety_zone(self, schema: SafetyZoneSchema) -> bool:
        """
        Add a new safety zone with empty sensor/appliance lists.

        Args:
            schema: Safety zone schema

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Insert new zone into database (empty sensors/appliances)
            if not self.storage_manager.insert_safety_zone(schema):
                return False

            # Get the newly created zone ID from database
            new_schema = self.storage_manager.get_safety_zone_by_name(
                schema.zone_name
            )
            if not new_schema:
                print(
                    f"Failed to load newly created \
                    safety zone {schema.zone_name}"
                )
                return False

            # Store in dictionary
            self.safety_zones[schema.zone_id] = SafetyZone(
                **new_schema.model_dump()
            )
            return True

        except Exception as e:
            print(f"Failed to add safety zone: {e}")
            return False

    def delete_safety_zone(self, zone_id: int) -> bool:
        """
        Delete a safety zone by ID.

        Args:
            zone_id (int): The zone ID to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Delete from database
            if not self.storage_manager.delete_safety_zone(zone_id):
                print(f"Failed to delete safety zone {zone_id}")
                return False

            # Remove from dictionary
            if zone_id in self.safety_zones:
                del self.safety_zones[zone_id]

            return True

        except Exception as e:
            print(f"Failed to delete safety zone: {e}")
            return False

    def arm_safety_zone(self, zone_id: int) -> bool:
        """
        Arm a safety zone by ID.
        """
        # get zone
        zone = self.get_safety_zone(zone_id)
        if not zone:
            print(f"Safety zone with id {zone_id} not found")
            return False

        # arm all sensors in the zone
        for sensor_id in zone.get_sensor_list():
            self.sensor_manager.arm_sensor(sensor_id)

        # update zone and database
        self._sync_zone_arm_state_with_sensors()
        self._update_all_sensors_in_db()
        self._update_all_zones_in_db()

        return True

    def disarm_safety_zone(self, zone_id: int) -> bool:
        """
        Disarm a safety zone by ID.
        """
        zone = self.get_safety_zone(zone_id)
        if not zone:
            print(f"Safety zone with id {zone_id} not found")
            return False

        # Disarm sensors in the zone
        for sensor_id in zone.get_sensor_list():
            self._disarm_sensor_in_zone(sensor_id, zone_id)

        # Update zone and database
        self._sync_zone_arm_state_with_sensors()
        self._update_all_sensors_in_db()
        self._update_all_zones_in_db()

        return True

    def _disarm_sensor_in_zone(self, sensor_id: int, zone_id: int) -> None:
        """
        Disarm a sensor, considering if it's needed by other zones.

        Motion detectors stay armed if another armed zone needs them
        and has other active sensors.
        """
        sensor = self.sensor_manager.get_sensor(sensor_id)
        if not sensor:
            return

        # Non-motion detectors: always disarm
        if sensor.get_type() != SensorType.MOTION_DETECTOR_SENSOR:
            self.sensor_manager.disarm_sensor(sensor_id)
            return

        # Motion detectors: check if needed by other zones
        if not self._is_sensor_needed_by_other_zones(sensor_id, zone_id):
            self.sensor_manager.disarm_sensor(sensor_id)

    def _is_sensor_needed_by_other_zones(
        self, sensor_id: int, excluded_zone_id: int
    ) -> bool:
        """
        Check if a motion detector is needed by other armed zones.

        A sensor is "needed" if it's in an armed zone that has
        other active sensors (i.e., zone isn't solely dependent on it).
        """
        for zone_id, zone in self.get_all_safety_zones().items():
            # Skip the zone being disarmed
            if zone_id == excluded_zone_id:
                continue

            # Check if zone is armed and contains this sensor
            if not zone.is_armed() or sensor_id not in zone.get_sensor_list():
                continue

            # Check if zone has other active sensors
            if self._zone_has_other_armed_sensors(zone, sensor_id):
                return True

        return False

    def _zone_has_other_armed_sensors(
        self,
        zone: SafetyZone,
        exclude_sensor_id: Optional[int] = None,
    ) -> bool:
        """
        Check if zone has any armed sensors.
        If exclude_sensor_id is provided, skip the sensor with the given ID.

        Args:
            zone: SafetyZone
            exclude_sensor_id: Optional[int] = None

        Returns:
            bool: True if zone has other armed sensors, False otherwise
        """
        for sensor_id in zone.get_sensor_list():
            if exclude_sensor_id and sensor_id == exclude_sensor_id:
                continue

            sensor = self.sensor_manager.sensor_dict.get(sensor_id)
            if sensor and sensor.is_armed():
                return True

        return False

    def _update_all_sensors_in_db(self) -> None:
        """
        Update all sensors in the database with current armed states.

        This syncs the armed status from memory (sensor_manager) to database.
        """
        if not self.sensor_manager:
            return

        for sensor in self.sensor_manager.sensor_dict.values():
            self.storage_manager.update_sensor(sensor)

    def _update_all_zones_in_db(self) -> None:
        """
        Update all zones in the database with current arm_status.

        This syncs the arm_status from memory to database.
        """
        for zone in self.get_all_safety_zones().values():
            zone_schema = zone.to_schema()
            self.storage_manager.update_safety_zone(zone_schema)

    def _check_zone_is_overlap(self, new_zone: SafetyZone) -> bool:
        """
        Check if the new zone is overlapping with any existing zone.
        """

        def _check_zone_is_overlap_with_zone(
            zone1: SafetyZone, zone2: SafetyZone
        ) -> bool:
            """
            Check if two zones overlap.
            Coordinates format: (x1, y1, x2, y2)
            Returns True if zones overlap, False otherwise.
            """
            coords1 = zone1.get_coordinates()
            coords2 = zone2.get_coordinates()

            # Two rectangles do NOT overlap if:
            # - zone1 is completely to the left of zone2
            # - zone1 is completely to the right of zone2
            # - zone1 is completely above zone2
            # - zone1 is completely below zone2
            if (
                coords1[2] <= coords2[0]  # zone1 left of zone2
                or coords1[0] >= coords2[2]  # zone1 right of zone2
                or coords1[3] <= coords2[1]  # zone1 above zone2
                or coords1[1] >= coords2[3]
            ):  # zone1 below zone2
                return False

            return True

        for zone in self.safety_zones.values():
            if new_zone.zone_id is not None:
                if zone.zone_id == new_zone.zone_id:
                    continue

            if _check_zone_is_overlap_with_zone(zone, new_zone):
                return True
        return False

    def _sync_zone_arm_state_with_sensors(self):
        """
        Sync the arm state of the zone with the sensors in the zone.
        - Any sensor armed -> Zone Armed
        - All sensors disarmed -> Zone Disarmed
        """
        if not self.sensor_manager:
            return

        for zone in self.get_all_safety_zones().values():
            if self._zone_has_other_armed_sensors(zone):
                zone.arm()
            else:
                zone.disarm()
