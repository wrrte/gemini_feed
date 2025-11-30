-- SafeHome Database Schema
-- SQLite3 Database Tables

-- Users Table
-- Stores user account information including homeowners and guests
-- HOMEOWNER: requires all fields (panel and web access)
-- GUEST: requires only panel_id and panel_password
--        (panel access only, panel password optional)
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    role TEXT NOT NULL CHECK(role IN ('HOMEOWNER', 'GUEST')),
    panel_id TEXT NOT NULL,
    panel_password TEXT,
    web_id TEXT,
    web_password TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        (role = 'HOMEOWNER' AND panel_password IS NOT NULL AND web_id IS NOT NULL AND web_password IS NOT NULL) OR
        (role = 'GUEST' AND panel_id IS NOT NULL AND web_id IS NULL AND web_password IS NULL)
    )
);

-- Logs Table
-- Stores application logs for monitoring and debugging
CREATE TABLE IF NOT EXISTS logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL CHECK(level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    filename TEXT,
    function_name TEXT,
    line_number INTEGER,
    message TEXT NOT NULL
);

-- SystemSettings Table
-- Stores system configuration key-value pairs
CREATE TABLE IF NOT EXISTS system_settings (
    system_setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
    panic_phone_number TEXT,
    homeowner_phone_number TEXT,
    system_lock_time INTEGER,
    alarm_delay_time INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sensors Table
-- Stores sensor information with zone assignment
CREATE TABLE IF NOT EXISTS sensors (
    sensor_id INTEGER PRIMARY KEY,
    sensor_type INTEGER NOT NULL,
    coordinate_x INTEGER NOT NULL,
    coordinate_y INTEGER NOT NULL,
    coordinate_x2 INTEGER,
    coordinate_y2 INTEGER,
    armed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Cameras Table
-- Stores camera information with zone assignment
CREATE TABLE IF NOT EXISTS cameras (
    camera_id     INTEGER PRIMARY KEY,
    coordinate_x  INTEGER NOT NULL,
    coordinate_y  INTEGER NOT NULL,
    pan           INTEGER NOT NULL CHECK (pan BETWEEN -3 AND 3),
    zoom_setting  INTEGER NOT NULL CHECK (zoom_setting BETWEEN 1 AND 5),
    has_password  INTEGER NOT NULL CHECK (has_password IN (0, 1)),
    password      TEXT,
    enabled       INTEGER NOT NULL CHECK (enabled IN (0, 1)),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (has_password = 0 OR password IS NOT NULL)
);

-- SafetyZone Table
-- Stores safety zone information including coordinates, sensors, and appliances
CREATE TABLE IF NOT EXISTS safety_zones (
    zone_id INTEGER PRIMARY KEY AUTOINCREMENT,
    zone_name TEXT NOT NULL UNIQUE,
    coordinate_x1 REAL,
    coordinate_y1 REAL,
    coordinate_x2 REAL,
    coordinate_y2 REAL,
    arm_status BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SafeHomeMode Table
-- Stores SafeHome mode information (Home, Away, Overnight, Extended Travel)
CREATE TABLE IF NOT EXISTS safehome_modes (
    mode_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mode_name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SafeHomeMode Sensors Table
-- Junction table for many-to-many relationship between modes and sensors
CREATE TABLE IF NOT EXISTS safehome_mode_sensors (
    mode_id INTEGER NOT NULL,
    sensor_id INTEGER NOT NULL,
    PRIMARY KEY (mode_id, sensor_id),
    FOREIGN KEY (mode_id) REFERENCES safehome_modes(mode_id) ON DELETE CASCADE
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
CREATE INDEX IF NOT EXISTS idx_configurations_key ON configurations(config_key);
CREATE INDEX IF NOT EXISTS idx_safety_zones_name ON safety_zones(zone_name);
CREATE INDEX IF NOT EXISTS idx_safehome_modes_name ON safehome_modes(mode_name);
CREATE INDEX IF NOT EXISTS idx_sensors_zone ON sensors(zone_id);
CREATE INDEX IF NOT EXISTS idx_appliances_zone ON appliances(zone_id);
CREATE INDEX IF NOT EXISTS idx_mode_sensors_mode ON safehome_mode_sensors(mode_id);
CREATE INDEX IF NOT EXISTS idx_mode_appliances_mode ON safehome_mode_appliances(mode_id);

