import os
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from database.schema.camera import CameraSchema
from database.schema.safehome_mode import SafeHomeModeSchema
from database.schema.safety_zone import SafetyZoneSchema
from database.schema.sensor import SensorSchema
from database.schema.system_setting import SystemSettingSchema


class StorageManager:
    """
    Database manager for SafeHome application using SQLite3.
    Implements singleton pattern to ensure single database connection.
    Provides CRUD operations for User, Log, and Configuration data.
    """

    _instance = None

    def __new__(
        cls,
        db_path: Optional[str] = None,
        db_file_name: Optional[str] = "safehome.db",
        reset_database: Optional[bool] = False,
    ) -> None:
        if cls._instance is None:
            cls._instance = super(StorageManager, cls).__new__(cls)
            cls._instance._initialize_database(
                db_path,
                db_file_name,
                reset_database,
            )
        return cls._instance

    def __init__(
        self,
        db_path: Optional[str] = None,
        db_file_name: Optional[str] = "safehome.db",
        reset_database: Optional[bool] = False,
    ) -> None:
        """
        Initialize instance.
        Note: Actual initialization is done in __new__ -> _initialize_database
        to ensure singleton pattern with one-time setup.
        """
        pass

    def _initialize_database(
        self,
        db_path: Optional[str] = None,
        db_file_name: Optional[str] = "safehome.db",
        reset_database: Optional[bool] = False,
    ) -> None:
        """Initialize database connection and create tables"""
        self.db_file_name = db_file_name
        self.reset_database = reset_database

        # Set database path
        if db_path:
            self.db_path = db_path
            # Create directory for custom db_path if it doesn't exist
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
        else:
            # Default: src/database/safehome.db
            base_dir = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
            db_dir = os.path.join(base_dir, "database")

            # Create database directory if it doesn't exist
            if not os.path.exists(db_dir):
                os.makedirs(db_dir)

            self.db_path = os.path.join(db_dir, self.db_file_name)

        # Initialize connection
        self.connection: Optional[sqlite3.Connection] = None
        self._connect()
        if self.reset_database:
            print("Dropping tables...")
            self._drop_tables()
            print("Creating tables...")
            self._create_tables()
            print("Initializing database data...")
            self._initialize_database_data()
        else:
            self._create_tables()

    def _connect(self):
        """Establish database connection"""
        try:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,  # Allow multi-threaded access
            )
            # Enable foreign key support
            self.connection.execute("PRAGMA foreign_keys = ON")
            # Return rows as dictionaries
            self.connection.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            print(f"Failed to connect to database: {e}")
            self.connection = None

    def _create_tables(self):
        """Create tables from SQL schema file"""
        if not self.connection:
            print("No database connection available")
            return

        try:
            # Find the SQL schema file
            base_dir = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
            sql_file_path = os.path.join(base_dir, "database", "safehome.sql")

            # Read and execute SQL schema
            if os.path.exists(sql_file_path):
                with open(sql_file_path, "r", encoding="utf-8") as f:
                    sql_script = f.read()

                cursor = self.connection.cursor()
                cursor.executescript(sql_script)
                self.connection.commit()
            else:
                print(f"SQL schema file not found: {sql_file_path}")
        except Exception as e:
            print(f"Failed to create tables: {e}")

    def _drop_tables(self):
        """Drop all tables from the database"""
        if not self.connection:
            print("No database connection available")
            return

        try:
            cursor = self.connection.cursor()

            # Get all table names (exclude sqlite internal tables)
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%'"
            )
            tables = cursor.fetchall()

            # Drop each table
            for table in tables:
                table_name = table[0]
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

            self.connection.commit()
            print(f"Dropped {len(tables)} tables successfully")
        except sqlite3.Error as e:
            print(f"Failed to drop tables: {e}")

    def _initialize_database_data(self):
        """Initialize database data"""
        if not self.connection:
            print("No database connection available")
            return

        try:
            base_dir = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
            sql_file_path = os.path.join(base_dir, "database", "init_data.sql")
            if os.path.exists(sql_file_path):
                with open(sql_file_path, "r", encoding="utf-8") as f:
                    sql_script = f.read()

                cursor = self.connection.cursor()
                cursor.executescript(sql_script)
                self.connection.commit()
                print("Database data initialized successfully")
            else:
                print(f"SQL data file not found: {sql_file_path}")
        except sqlite3.Error as e:
            print(f"Failed to initialize database data: {e}")
            raise e

    def execute_query(
        self, query: str, params: Optional[Tuple] = None
    ) -> Optional[List[sqlite3.Row]]:
        """
        Execute a raw SQL query

        Args:
            query: SQL query string
            params: Query parameters tuple

        Returns:
            List of rows for SELECT queries, empty list for successful
            INSERT/UPDATE/DELETE, None for errors
        """
        if not self.connection:
            return None

        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # If it's a SELECT query, fetch results
            if query.strip().upper().startswith("SELECT"):
                return cursor.fetchall()
            else:
                self.connection.commit()
                return []  # Return empty list for successful non-SELECT
        except sqlite3.Error as e:
            print(f"Query execution failed: {e}")
            return None

    # ==================== User CRUD Operations ====================

    def insert_user(
        self,
        user_id: str,
        role: str,
        panel_id: str,
        panel_password: str,
        web_id: Optional[str] = None,
        web_password: Optional[str] = None,
    ) -> bool:
        """
        Insert a new user into the database

        Args:
            user_id: Unique user identifier
            role: User role (ADMINHOMEOWNER, HOMEOWNER, GUEST)
            panel_id: Panel login ID
            panel_password: Panel login password
            web_id: Web login ID
            web_password: Web login password

        Returns:
            True if successful, False otherwise
        """
        query = """
            INSERT INTO users
            (user_id, role, panel_id, panel_password, web_id, web_password)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        result = self.execute_query(
            query,
            (user_id, role, panel_id, panel_password, web_id, web_password),
        )
        return result is not None

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user by user_id

        Args:
            user_id: User identifier

        Returns:
            Dictionary containing user data, None if not found
        """
        query = "SELECT * FROM users WHERE user_id = ?"
        rows = self.execute_query(query, (user_id,))

        if rows and len(rows) > 0:
            return dict(rows[0])
        return None

    def update_user(self, user_id: str, **kwargs) -> bool:
        """
        Update user information

        Args:
            user_id: User identifier
            **kwargs: Fields to update
                (role, panel_id, panel_password, web_id, web_password)

        Returns:
            True if successful, False otherwise
        """
        if not kwargs:
            return False

        # Build dynamic UPDATE query
        valid_fields = [
            "role",
            "panel_id",
            "panel_password",
            "web_id",
            "web_password",
        ]
        update_fields = []
        values = []

        for key, value in kwargs.items():
            if key in valid_fields:
                update_fields.append(f"{key} = ?")
                values.append(value)

        if not update_fields:
            return False

        values.append(user_id)
        query = (
            f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = ?"
        )

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, tuple(values))
            self.connection.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Failed to update user: {e}")
            return False

    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user from the database

        Args:
            user_id: User identifier

        Returns:
            True if successful, False otherwise
        """
        query = "DELETE FROM users WHERE user_id = ?"
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (user_id,))
            self.connection.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Failed to delete user: {e}")
            return False

    # ==================== Log CRUD Operations ====================

    def insert_log(
        self,
        level: str,
        message: str,
        filename: Optional[str] = None,
        function_name: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> bool:
        """
        Insert a log entry into the database

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            filename: Source file name
            function_name: Function name where log originated
            line_number: Line number where log originated

        Returns:
            True if successful, False otherwise
        """
        query = """
            INSERT INTO logs (level, filename, function_name,
                                line_number, message)
            VALUES (?, ?, ?, ?, ?)
        """
        result = self.execute_query(
            query, (level, filename, function_name, line_number, message)
        )
        return result is not None

    def get_logs(
        self, limit: Optional[int] = 100, level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve logs from the database

        Args:
            limit: Maximum number of logs to retrieve
            level: Filter by log level (optional)

        Returns:
            List of log dictionaries
        """
        if level:
            query = """
                SELECT * FROM logs
                WHERE level = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """
            rows = self.execute_query(query, (level, limit))
        else:
            query = """
                SELECT * FROM logs
                ORDER BY timestamp DESC
                LIMIT ?
            """
            rows = self.execute_query(query, (limit,))

        if rows:
            return [dict(row) for row in rows]
        return []

    def delete_logs_before(self, timestamp: str) -> bool:
        """
        Delete logs older than specified timestamp

        Args:
            timestamp: ISO format timestamp string
                (e.g., '2024-01-01 00:00:00')

        Returns:
            True if successful, False otherwise
        """
        query = "DELETE FROM logs WHERE timestamp < ?"
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (timestamp,))
            self.connection.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Failed to delete logs: {e}")
            return False

    # ==================== SystemSettings CRUD Operations ====================

    def insert_system_setting(
        self, system_setting: SystemSettingSchema
    ) -> bool:
        """
        Insert a new system setting into the database

        Args:
            system_setting: System setting schema

        Returns:
            True if successful, False otherwise
        """
        query = """
            INSERT INTO system_settings
            (
                panic_phone_number,
                homeowner_phone_number,
                system_lock_time,
                alarm_delay_time
            )
            VALUES (?, ?, ?, ?)
        """
        result = self.execute_query(
            query,
            (
                system_setting.panic_phone_number,
                system_setting.homeowner_phone_number,
                system_setting.system_lock_time,
                system_setting.alarm_delay_time,
            ),
        )
        return result is not None

    def update_system_setting(
        self, system_setting: SystemSettingSchema
    ) -> bool:
        """
        Update a system setting entry

        Args:
            system_setting: System setting schema

        Returns:
            True if successful, False otherwise
        """
        query = """
            UPDATE system_settings
            SET panic_phone_number = ?,
                homeowner_phone_number = ?,
                system_lock_time = ?,
                alarm_delay_time = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE system_setting_id = ?
        """
        result = self.execute_query(
            query,
            (
                system_setting.panic_phone_number,
                system_setting.homeowner_phone_number,
                system_setting.system_lock_time,
                system_setting.alarm_delay_time,
                system_setting.system_setting_id,
            ),
        )
        return result is not None

    def get_system_setting(
        self, system_setting_id: int
    ) -> Optional[SystemSettingSchema]:
        """
        Retrieve a system setting by its ID.
        """
        query = "SELECT * FROM system_settings WHERE system_setting_id = ?"
        rows = self.execute_query(query, (system_setting_id,))

        if rows and len(rows) > 0:
            return SystemSettingSchema(**rows[0])
        return None

    def delete_system_setting(self, system_setting_id: int) -> bool:
        """
        Delete a system setting by its ID.

        Args:
            system_setting_id: System setting ID

        Returns:
            True if deleted, False if not found or error
        """
        query = "DELETE FROM system_settings WHERE system_setting_id = ?"
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (system_setting_id,))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Failed to delete system setting: {e}")
            return False

    # ==================== SafeHomeMode Operations ====================

    def get_all_safehome_modes(self) -> List[SafeHomeModeSchema]:
        """
        Get all SafeHome modes from database with their sensor IDs.

        Returns:
            List of SafeHome mode schemas
        """
        query = """
            SELECT
                sm.mode_id,
                sm.mode_name,
                sm.created_at,
                sm.updated_at,
                GROUP_CONCAT(sms.sensor_id) as sensor_ids
            FROM safehome_modes sm
            LEFT JOIN safehome_mode_sensors sms ON sm.mode_id = sms.mode_id
            GROUP BY sm.mode_id, sm.mode_name, sm.created_at, sm.updated_at
        """
        rows = self.execute_query(query)
        if not rows:
            return []

        safehome_modes = []
        for row in rows:
            # Convert GROUP_CONCAT result to list of integers
            sensor_ids_str = row["sensor_ids"]
            sensor_ids = (
                [int(sid) for sid in sensor_ids_str.split(",")]
                if sensor_ids_str
                else []
            )

            mode = SafeHomeModeSchema(
                mode_id=row["mode_id"],
                mode_name=row["mode_name"],
                sensor_ids=sensor_ids,
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            safehome_modes.append(mode)

        return safehome_modes

    def get_safehome_mode_sensors(self, mode_id: int) -> List[int]:
        """
        Get sensor IDs for a specific SafeHome mode.

        Args:
            mode_id: SafeHome mode ID

        Returns:
            List of sensor IDs
        """
        query = """SELECT sensor_id FROM safehome_mode_sensors
                   WHERE mode_id = ?
                   ORDER BY sensor_id"""
        rows = self.execute_query(query, (mode_id,))
        if rows:
            sensor_ids = [row["sensor_id"] for row in rows]
            return sensor_ids
        return []

    def insert_safehome_mode(self, schema: SafeHomeModeSchema) -> bool:
        """
        Insert a new SafeHome mode with sensor lists.

        Args:
            schema: SafeHomeMode schema with mode_name and sensor_ids

        Returns:
            True if successful, False otherwise
        """
        try:
            # Insert the mode
            query = """INSERT INTO safehome_modes (mode_name) VALUES (?)"""
            cursor = self.connection.cursor()
            cursor.execute(query, (schema.mode_name,))
            self.connection.commit()

            # Get the newly created mode_id
            new_mode_id = cursor.lastrowid

            # Insert sensors if provided
            if schema.sensor_ids:
                insert_sensor_query = """
                    INSERT INTO safehome_mode_sensors (mode_id, sensor_id)
                    VALUES (?, ?)
                """
                for sensor_id in schema.sensor_ids:
                    cursor.execute(
                        insert_sensor_query, (new_mode_id, sensor_id)
                    )
                self.connection.commit()

            return True
        except Exception as e:
            print(f"Failed to insert safehome mode: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    def update_safehome_mode(self, schema: SafeHomeModeSchema) -> bool:
        """
        Update a SafeHome mode with sensor lists.

        Args:
            schema: SafeHomeMode schema with mode_name and sensor_ids

        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.connection.cursor()

            # Update the mode
            query = """
                UPDATE
                safehome_modes
                SET mode_name = ?,
                updated_at = CURRENT_TIMESTAMP
                WHERE mode_id = ?
            """
            cursor.execute(query, (schema.mode_name, schema.mode_id))

            # Delete existing sensors
            delete_query = """
                DELETE FROM safehome_mode_sensors WHERE mode_id = ?
            """
            cursor.execute(delete_query, (schema.mode_id,))

            # Insert new sensors
            if schema.sensor_ids:
                insert_sensor_query = """
                    INSERT INTO safehome_mode_sensors (mode_id, sensor_id)
                    VALUES (?, ?)
                """
                for sensor_id in schema.sensor_ids:
                    cursor.execute(
                        insert_sensor_query, (schema.mode_id, sensor_id)
                    )

            self.connection.commit()
            return True
        except Exception as e:
            print(f"Failed to update safehome mode: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    # ==================== SafetyZone Operations ====================

    def get_all_safety_zones(self) -> List[SafetyZoneSchema]:
        """
        Get all safety zones from database.

        Returns:
            List of safety zone schemas
        """
        query = "SELECT * FROM safety_zones"
        rows = self.execute_query(query)
        if rows and len(rows) > 0:
            return [SafetyZoneSchema(**row) for row in rows]
        return []

    def get_safety_zone(self, zone_id: int) -> Optional[SafetyZoneSchema]:
        """
        Get a safety zone by its ID.
        """
        query = "SELECT * FROM safety_zones WHERE zone_id = ?"
        rows = self.execute_query(query, (zone_id,))
        if rows and len(rows) > 0:
            return SafetyZoneSchema(**rows[0])
        return None

    def update_safety_zone(self, zone: SafetyZoneSchema) -> bool:
        """
        Update a specific field of safety zone.

        Args:
            zone: Safety zone schema

        Returns:
            True if successful, False otherwise
        """
        try:
            query = """UPDATE safety_zones
                       SET zone_name = ?,
                           coordinate_x1 = ?,
                           coordinate_y1 = ?,
                           coordinate_x2 = ?,
                           coordinate_y2 = ?,
                           arm_status = ?,
                           updated_at = CURRENT_TIMESTAMP
                       WHERE zone_id = ?"""
            result = self.execute_query(
                query,
                (
                    zone.zone_name,
                    zone.coordinate_x1,
                    zone.coordinate_y1,
                    zone.coordinate_x2,
                    zone.coordinate_y2,
                    zone.arm_status,
                    zone.zone_id,
                ),
            )
            return result is not None

        except Exception as e:
            print(f"Failed to update safety zone: {e}")
            return False

    def insert_safety_zone(self, zone: SafetyZoneSchema) -> bool:
        """
        Insert a new safety zone with empty coordinates/sensor/appliance.

        Args:
            zone: Safety zone schema

        Returns:
            True if successful, False otherwise
        """
        query = """INSERT INTO safety_zones
            (zone_name,
            coordinate_x1,
            coordinate_y1,
            coordinate_x2,
            coordinate_y2,
            arm_status,
            created_at,
            updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        result = self.execute_query(
            query,
            (
                zone.zone_name,
                zone.coordinate_x1,
                zone.coordinate_y1,
                zone.coordinate_x2,
                zone.coordinate_y2,
                zone.arm_status,
            ),
        )
        return result is not None

    def get_safety_zone_by_name(
        self, zone_name: str
    ) -> Optional[SafetyZoneSchema]:
        """
        Get safety zone by name.

        Args:
            zone_name: Zone name

        Returns:
            Safety zone schema or None
        """
        query = "SELECT * FROM safety_zones WHERE zone_name = ?"
        rows = self.execute_query(query, (zone_name,))
        if rows and len(rows) > 0:
            return SafetyZoneSchema(**rows[0])
        return None

    def delete_safety_zone(self, zone_id: int) -> bool:
        """
        Delete a safety zone from the database

        Args:
            zone_id: Zone ID

        Returns:
            True if successful, False otherwise
        """
        query = "DELETE FROM safety_zones WHERE zone_id = ?"
        result = self.execute_query(query, (zone_id,))
        return result is not None

    # ==================== Sensor Operations ====================

    def get_all_sensors(self) -> List[SensorSchema]:
        """
        Get all sensors from database.

        Returns:
            List of sensor schemas
        """
        query = "SELECT * FROM sensors"
        rows = self.execute_query(query)
        if rows:
            return [SensorSchema(**row) for row in rows]
        return []

    def get_sensor_by_id(self, sensor_id: int) -> Optional[SensorSchema]:
        """
        Get a sensor by its ID.

        Args:
            sensor_id: Sensor ID

        Returns:
            Sensor dictionary or None
        """
        query = "SELECT * FROM sensors WHERE sensor_id = ?"
        rows = self.execute_query(query, (sensor_id,))
        if rows and len(rows) > 0:
            return SensorSchema(**rows[0])
        return None

    def update_sensor(self, sensor: SensorSchema) -> bool:
        """
        Update a sensor.

        Args:
            sensor: Sensor schema

        Returns:
            True if successful, False otherwise
        """
        query = """
        UPDATE sensors
        SET sensor_type = ?,
            coordinate_x = ?,
            coordinate_y = ?,
            coordinate_x2 = ?,
            coordinate_y2 = ?,
            armed = ?,
            updated_at = CURRENT_TIMESTAMP
            WHERE sensor_id = ?
        """
        result = self.execute_query(
            query,
            (
                sensor.sensor_type.value,
                sensor.coordinate_x,
                sensor.coordinate_y,
                sensor.coordinate_x2,
                sensor.coordinate_y2,
                sensor.armed,
                sensor.sensor_id,
            ),
        )
        return result is not None

    # ==================== Camera Operations ====================

    def get_all_cameras(self) -> List[CameraSchema]:
        """
        Get all cameras from database.

        Returns:
            List of sensor cameras
        """
        query = "SELECT * FROM cameras"
        rows = self.execute_query(query)
        if rows:
            return [CameraSchema(**row) for row in rows]
        return []

    def update_camera(self, camera: CameraSchema) -> bool:
        """
        Update camera information.

        Args:
            camera: Camera schema

        Returns:
            True if successful, False otherwise
        """
        query = """UPDATE cameras
                   SET coordinate_x = ?,
                       coordinate_y = ?,
                       pan = ?,
                       zoom_setting = ?,
                       has_password = ?,
                       password = ?,
                       enabled = ?,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE camera_id = ?"""
        result = self.execute_query(
            query,
            (
                camera.coordinate_x,
                camera.coordinate_y,
                camera.pan,
                camera.zoom_setting,
                camera.has_password,
                camera.password,
                camera.enabled,
                camera.camera_id,
            ),
        )
        return result is not None

    # ==================== Utility Methods ====================
    def close(self):
        """Close the database connection"""
        if self.connection:
            try:
                self.connection.close()
                self.connection = None
            except sqlite3.Error as e:
                print(f"Failed to close database connection: {e}")

    def clean_up(self):
        """Clean up the storage manager"""
        self.close()
        StorageManager._instance = None

    def __del__(self):
        """Cleanup: close connection when object is destroyed"""
        self.close()
        StorageManager._instance = None
