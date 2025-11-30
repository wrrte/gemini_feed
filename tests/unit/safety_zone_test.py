from datetime import datetime

from configurations.safety_zone import SafetyZone


def test_safety_zone_initialization():
    """Test SafetyZone initialization with all parameters"""
    zone = SafetyZone(
        zone_id=1,
        zone_name="Living Room",
        coordinate_x1=10.0,
        coordinate_y1=20.0,
        coordinate_x2=100.0,
        coordinate_y2=200.0,
        sensor_id_list=[1, 2, 3],
        arm_status=True,
    )

    assert zone.get_zone_id() == 1
    assert zone.get_zone_name() == "Living Room"
    assert zone.get_coordinates() == (10.0, 20.0, 100.0, 200.0)
    assert zone.get_sensor_list() == [1, 2, 3]
    assert zone.is_armed() is True


def test_safety_zone_initialization_defaults():
    """Test SafetyZone initialization with default values"""
    zone = SafetyZone(
        zone_id=2,
        zone_name="Bedroom",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=50.0,
        coordinate_y2=50.0,
    )

    assert zone.get_zone_id() == 2
    assert zone.get_sensor_list() == []
    assert zone.is_armed() is False


def test_safety_zone_set_id():
    """Test setting zone ID"""
    zone = SafetyZone(
        zone_id=1,
        zone_name="Test",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
    )

    result = zone.set_id(5)
    assert result is True
    assert zone.get_zone_id() == 5


def test_safety_zone_set_id_invalid():
    """Test setting invalid zone ID"""
    zone = SafetyZone(
        zone_id=1,
        zone_name="Test",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
    )

    result = zone.set_id("not_an_int")
    assert result is False
    assert zone.get_zone_id() == 1  # Should remain unchanged


def test_safety_zone_set_zone_name():
    """Test setting zone name"""
    zone = SafetyZone(
        zone_id=1,
        zone_name="Old Name",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
    )

    result = zone.set_zone_name("New Name")
    assert result is True
    assert zone.get_zone_name() == "New Name"


def test_safety_zone_set_zone_name_invalid():
    """Test setting invalid zone name"""
    zone = SafetyZone(
        zone_id=1,
        zone_name="Valid Name",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
    )

    result = zone.set_zone_name(12345)
    assert result is False
    assert zone.get_zone_name() == "Valid Name"


def test_safety_zone_set_coordinates():
    """Test setting coordinates"""
    zone = SafetyZone(
        zone_id=1,
        zone_name="Test",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
    )

    result = zone.set_coordinates(5.0, 15.0, 25.0, 35.0)
    assert result is True
    assert zone.get_coordinates() == (5.0, 15.0, 25.0, 35.0)


def test_safety_zone_set_coordinates_with_integers():
    """Test setting coordinates with integer values"""
    zone = SafetyZone(
        zone_id=1,
        zone_name="Test",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
    )

    result = zone.set_coordinates(5, 15, 25, 35)
    assert result is True
    assert zone.get_coordinates() == (5, 15, 25, 35)


def test_safety_zone_set_coordinates_invalid():
    """Test setting invalid coordinates"""
    zone = SafetyZone(
        zone_id=1,
        zone_name="Test",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
    )

    result = zone.set_coordinates("invalid", 15.0, 25.0, 35.0)
    assert result is False
    # Coordinates should remain unchanged
    assert zone.get_coordinates() == (0.0, 0.0, 10.0, 10.0)


def test_safety_zone_set_sensor_list():
    """Test setting sensor list"""
    zone = SafetyZone(
        zone_id=1,
        zone_name="Test",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
    )

    result = zone.set_sensor_list([10, 20, 30])
    assert result is True
    assert zone.get_sensor_list() == [10, 20, 30]


def test_safety_zone_set_sensor_list_invalid_type():
    """Test setting sensor list with invalid type"""
    zone = SafetyZone(
        zone_id=1,
        zone_name="Test",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
        sensor_id_list=[1, 2],
    )

    result = zone.set_sensor_list("not a list")
    assert result is False
    assert zone.get_sensor_list() == [1, 2]


def test_safety_zone_set_sensor_list_invalid_elements():
    """Test setting sensor list with non-integer elements"""
    zone = SafetyZone(
        zone_id=1,
        zone_name="Test",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
        sensor_id_list=[1, 2],
    )

    result = zone.set_sensor_list([1, "2", 3])
    assert result is False
    assert zone.get_sensor_list() == [1, 2]


def test_safety_zone_get_sensor_list_returns_copy():
    """Test that get_sensor_list returns a copy"""
    zone = SafetyZone(
        zone_id=1,
        zone_name="Test",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
        sensor_id_list=[1, 2, 3],
    )

    sensor_list = zone.get_sensor_list()
    sensor_list.append(4)

    # Original should not be modified
    assert zone.get_sensor_list() == [1, 2, 3]


def test_safety_zone_add_sensor():
    """Test adding a single sensor"""
    zone = SafetyZone(
        zone_id=1,
        zone_name="Test",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
        sensor_id_list=[1, 2],
    )

    result = zone.add_sensor(3)
    assert result is True
    assert zone.get_sensor_list() == [1, 2, 3]


def test_safety_zone_add_sensor_duplicate():
    """Test adding a duplicate sensor"""
    zone = SafetyZone(
        zone_id=1,
        zone_name="Test",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
        sensor_id_list=[1, 2, 3],
    )

    result = zone.add_sensor(2)
    assert result is False
    assert zone.get_sensor_list() == [1, 2, 3]


def test_safety_zone_add_sensor_invalid_type():
    """Test adding invalid sensor type"""
    zone = SafetyZone(
        zone_id=1,
        zone_name="Test",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
        sensor_id_list=[1, 2],
    )

    result = zone.add_sensor("not_int")
    assert result is False
    assert zone.get_sensor_list() == [1, 2]


def test_safety_zone_remove_sensor():
    """Test removing a sensor"""
    zone = SafetyZone(
        zone_id=1,
        zone_name="Test",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
        sensor_id_list=[1, 2, 3],
    )

    result = zone.remove_sensor(2)
    assert result is True
    assert zone.get_sensor_list() == [1, 3]


def test_safety_zone_remove_sensor_not_found():
    """Test removing a sensor that doesn't exist"""
    zone = SafetyZone(
        zone_id=1,
        zone_name="Test",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
        sensor_id_list=[1, 2, 3],
    )

    result = zone.remove_sensor(5)
    assert result is False
    assert zone.get_sensor_list() == [1, 2, 3]


def test_safety_zone_delete_all_sensors():
    """Test deleting all sensors"""
    zone = SafetyZone(
        zone_id=1,
        zone_name="Test",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
        sensor_id_list=[1, 2, 3, 4, 5],
    )

    zone.delete_all_sensors()
    assert zone.get_sensor_list() == []


def test_safety_zone_is_armed():
    """Test is_armed method"""
    zone_armed = SafetyZone(
        zone_id=1,
        zone_name="Test",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
        arm_status=True,
    )

    zone_disarmed = SafetyZone(
        zone_id=2,
        zone_name="Test2",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
        arm_status=False,
    )

    assert zone_armed.is_armed() is True
    assert zone_disarmed.is_armed() is False


def test_safety_zone_arm():
    """Test arming a zone"""
    zone = SafetyZone(
        zone_id=1,
        zone_name="Test",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
        arm_status=False,
    )

    assert zone.is_armed() is False
    zone.arm()
    assert zone.is_armed() is True


def test_safety_zone_disarm():
    """Test disarming a zone"""
    zone = SafetyZone(
        zone_id=1,
        zone_name="Test",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
        arm_status=True,
    )

    assert zone.is_armed() is True
    zone.disarm()
    assert zone.is_armed() is False


def test_safety_zone_arm_disarm_toggle():
    """Test multiple arm/disarm toggles"""
    zone = SafetyZone(
        zone_id=1,
        zone_name="Test",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
    )

    assert zone.is_armed() is False

    zone.arm()
    assert zone.is_armed() is True

    zone.arm()  # Arm again
    assert zone.is_armed() is True

    zone.disarm()
    assert zone.is_armed() is False

    zone.disarm()  # Disarm again
    assert zone.is_armed() is False


def test_safety_zone_to_schema():
    """Test conversion to SafetyZoneSchema"""
    now = datetime.now()
    zone = SafetyZone(
        zone_id=1,
        zone_name="Test Zone",
        coordinate_x1=10.0,
        coordinate_y1=20.0,
        coordinate_x2=100.0,
        coordinate_y2=200.0,
        sensor_id_list=[1, 2, 3],
        arm_status=True,
        created_at=now,
        updated_at=now,
    )

    schema = zone.to_schema()

    assert schema.zone_id == 1
    assert schema.zone_name == "Test Zone"
    assert schema.coordinate_x1 == 10.0
    assert schema.coordinate_y1 == 20.0
    assert schema.coordinate_x2 == 100.0
    assert schema.coordinate_y2 == 200.0
    assert schema.sensor_id_list == [1, 2, 3]
    assert schema.arm_status is True
    assert schema.created_at == now
    assert schema.updated_at == now


def test_safety_zone_str():
    """Test string representation"""
    zone_armed = SafetyZone(
        zone_id=1,
        zone_name="Living Room",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
        sensor_id_list=[1, 2, 3],
        arm_status=True,
    )

    zone_disarmed = SafetyZone(
        zone_id=2,
        zone_name="Bedroom",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
        sensor_id_list=[4, 5],
        arm_status=False,
    )

    str_armed = str(zone_armed)
    assert "ID=1" in str_armed
    assert "Living Room" in str_armed
    assert "Sensors=3" in str_armed
    assert "ARMED" in str_armed

    str_disarmed = str(zone_disarmed)
    assert "ID=2" in str_disarmed
    assert "Bedroom" in str_disarmed
    assert "Sensors=2" in str_disarmed
    assert "DISARMED" in str_disarmed


def test_safety_zone_sensor_list_initialization_with_none():
    """Test that sensor_id_list handles None initialization"""
    zone = SafetyZone(
        zone_id=1,
        zone_name="Test",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
        sensor_id_list=None,
    )

    assert zone.get_sensor_list() == []


def test_safety_zone_coordinates_with_negative_values():
    """Test coordinates with negative values"""
    zone = SafetyZone(
        zone_id=1,
        zone_name="Test",
        coordinate_x1=-10.0,
        coordinate_y1=-20.0,
        coordinate_x2=30.0,
        coordinate_y2=40.0,
    )

    assert zone.get_coordinates() == (-10.0, -20.0, 30.0, 40.0)


def test_safety_zone_set_coordinates_negative_values():
    """Test setting coordinates with negative values"""
    zone = SafetyZone(
        zone_id=1,
        zone_name="Test",
        coordinate_x1=0.0,
        coordinate_y1=0.0,
        coordinate_x2=10.0,
        coordinate_y2=10.0,
    )

    result = zone.set_coordinates(-50.0, -100.0, 50.0, 100.0)
    assert result is True
    assert zone.get_coordinates() == (-50.0, -100.0, 50.0, 100.0)
