-- Initialize Database Data
BEGIN TRANSACTION;

-- Insert default users
INSERT INTO users (user_id, role, panel_id, panel_password, web_id, web_password) VALUES
  ('admin', 'HOMEOWNER', 'master', '1234', 'master', '12345678'),
  ('guest', 'GUEST', 'guest', NULL, NULL, NULL);

-- Insert default system settings
INSERT INTO system_settings (system_setting_id, panic_phone_number, homeowner_phone_number, system_lock_time, alarm_delay_time) VALUES
  (1, '119', '010-0000-0000', 3, 3);

-- Insert default sensors
-- SensorType: 1=WINDOOR_SENSOR, 2=MOTION_DETECTOR_SENSOR
INSERT INTO sensors (sensor_id, sensor_type, coordinate_x, coordinate_y, coordinate_x2, coordinate_y2, armed) VALUES
  (1, 1, 240,  10, NULL, NULL, FALSE),
  (2, 1,  85, 300, NULL, NULL, FALSE),
  (3, 1,  70,  10, NULL, NULL, FALSE),
  (4, 1, 395,  10, NULL, NULL, FALSE),
  (5, 1, 490, 80, NULL, NULL, FALSE),
  (6, 1, 490,  215, NULL, NULL, FALSE),
  (7, 1,   5, 210, NULL, NULL, FALSE),
  (8, 1,   5,  80, NULL, NULL, FALSE),
  (9, 2,  30,  80, 470, 80, FALSE),
  (10,2, 150, 170, 5, 270, FALSE);

INSERT INTO cameras (camera_id, coordinate_x, coordinate_y, pan, zoom_setting, has_password, password, enabled) VALUES
  (1, 390, 270, 0, 1, 0, NULL, 1),
  (2, 110, 35, 0, 1, 0, NULL, 1),
  (3, 220, 200, 0, 1, 0, NULL, 1);

INSERT INTO safety_zones (zone_id, zone_name, coordinate_x1, coordinate_x2, coordinate_y1, coordinate_y2) VALUES
  (1, 'Dining Room', 0, 170, 0, 120),
  (2, 'Kitchen', 0,  150, 150, 312),
  (3, 'Living Room Top', 310, 500, 0, 120),
  (4, 'Living Room Bottom', 300, 500, 170, 312);

-- [추가] SafeHome Modes 기본 데이터 삽입
INSERT INTO safehome_modes (mode_id, mode_name) VALUES
  (1, 'Away'),
  (2, 'Home'),
  (3, 'Overnight Travel'),
  (4, 'Extended Travel'),
  (5, 'Guest Home');

INSERT INTO safehome_mode_sensors (mode_id, sensor_id) VALUES
  (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10);

INSERT INTO safehome_mode_sensors (mode_id, sensor_id) VALUES
  (3, 1), (3, 3), (3, 5), (3, 7), (3, 9);

INSERT INTO safehome_mode_sensors (mode_id, sensor_id) VALUES
  (4, 2), (4, 4), (4, 6), (4, 8), (4, 10);

INSERT INTO safehome_mode_sensors (mode_id, sensor_id) VALUES
  (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7), (5, 8);

COMMIT;


