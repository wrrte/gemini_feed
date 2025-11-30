from datetime import datetime

from configurations.safehome_mode import SafeHomeMode


def test_safehome_mode_initialization():
    """Test SafeHomeMode initialization with all parameters"""
    now = datetime.now()
    mode = SafeHomeMode(
        mode_id=1,
        mode_name="Home",
        sensor_ids=[1, 2, 3],
        created_at=now,
        updated_at=now,
    )

    assert mode.get_id() == 1
    assert mode.get_mode_name() == "Home"
    assert mode.get_sensor_list() == [1, 2, 3]
    assert mode.created_at == now
    assert mode.updated_at == now


def test_safehome_mode_initialization_empty_sensors():
    """Test SafeHomeMode initialization with empty sensor list"""
    mode = SafeHomeMode(
        mode_id=2,
        mode_name="Away",
        sensor_ids=[],
    )

    assert mode.get_id() == 2
    assert mode.get_mode_name() == "Away"
    assert mode.get_sensor_list() == []


def test_safehome_mode_initialization_none_sensors():
    """Test SafeHomeMode initialization with None sensor list"""
    mode = SafeHomeMode(
        mode_id=3,
        mode_name="Overnight",
        sensor_ids=None,
    )

    assert mode.get_sensor_list() == []


def test_safehome_mode_initialization_copies_sensor_list():
    """Test that initialization creates a copy of sensor list"""
    original_list = [1, 2, 3]
    mode = SafeHomeMode(
        mode_id=1,
        mode_name="Home",
        sensor_ids=original_list,
    )

    # Modify original list
    original_list.append(4)

    # Mode's sensor list should be unaffected
    assert mode.get_sensor_list() == [1, 2, 3]


def test_safehome_mode_set_id():
    """Test setting mode ID with valid integer"""
    mode = SafeHomeMode(
        mode_id=1,
        mode_name="Home",
        sensor_ids=[],
    )

    result = mode.set_id(5)
    assert result is True
    assert mode.get_id() == 5


def test_safehome_mode_set_id_invalid():
    """Test setting mode ID with invalid type"""
    mode = SafeHomeMode(
        mode_id=1,
        mode_name="Home",
        sensor_ids=[],
    )

    result = mode.set_id("not_an_int")
    assert result is False
    assert mode.get_id() == 1  # Should remain unchanged


def test_safehome_mode_get_id():
    """Test getting mode ID"""
    mode = SafeHomeMode(
        mode_id=42,
        mode_name="Home",
        sensor_ids=[],
    )

    assert mode.get_id() == 42


def test_safehome_mode_get_mode_name():
    """Test getting mode name"""
    mode = SafeHomeMode(
        mode_id=1,
        mode_name="Extended Travel",
        sensor_ids=[],
    )

    assert mode.get_mode_name() == "Extended Travel"


def test_safehome_mode_set_sensor_list():
    """Test setting sensor list"""
    mode = SafeHomeMode(
        mode_id=1,
        mode_name="Home",
        sensor_ids=[1, 2],
    )

    result = mode.set_sensor_list([10, 20, 30])
    assert result is True
    assert mode.get_sensor_list() == [10, 20, 30]


def test_safehome_mode_set_sensor_list_creates_copy():
    """Test that set_sensor_list creates a copy"""
    mode = SafeHomeMode(
        mode_id=1,
        mode_name="Home",
        sensor_ids=[],
    )

    new_list = [5, 6, 7]
    mode.set_sensor_list(new_list)

    # Modify original list
    new_list.append(8)

    # Mode's sensor list should be unaffected
    assert mode.get_sensor_list() == [5, 6, 7]


def test_safehome_mode_get_sensor_list_returns_copy():
    """Test that get_sensor_list returns a copy"""
    mode = SafeHomeMode(
        mode_id=1,
        mode_name="Home",
        sensor_ids=[1, 2, 3],
    )

    sensor_list = mode.get_sensor_list()
    sensor_list.append(4)

    # Original should not be modified
    assert mode.get_sensor_list() == [1, 2, 3]


def test_safehome_mode_add_sensor():
    """Test adding a new sensor"""
    mode = SafeHomeMode(
        mode_id=1,
        mode_name="Home",
        sensor_ids=[1, 2],
    )

    result = mode.add_sensor(3)
    assert result is True
    assert mode.get_sensor_list() == [1, 2, 3]


def test_safehome_mode_add_sensor_duplicate():
    """Test adding a duplicate sensor"""
    mode = SafeHomeMode(
        mode_id=1,
        mode_name="Home",
        sensor_ids=[1, 2, 3],
    )

    result = mode.add_sensor(2)
    assert result is False
    assert mode.get_sensor_list() == [1, 2, 3]


def test_safehome_mode_add_sensor_invalid_type():
    """Test adding sensor with invalid type"""
    mode = SafeHomeMode(
        mode_id=1,
        mode_name="Home",
        sensor_ids=[1, 2],
    )

    result = mode.add_sensor("not_int")
    assert result is False
    assert mode.get_sensor_list() == [1, 2]


def test_safehome_mode_remove_sensor():
    """Test removing an existing sensor"""
    mode = SafeHomeMode(
        mode_id=1,
        mode_name="Home",
        sensor_ids=[1, 2, 3],
    )

    result = mode.remove_sensor(2)
    assert result is True
    assert mode.get_sensor_list() == [1, 3]


def test_safehome_mode_remove_sensor_not_found():
    """Test removing a non-existent sensor"""
    mode = SafeHomeMode(
        mode_id=1,
        mode_name="Home",
        sensor_ids=[1, 2, 3],
    )

    result = mode.remove_sensor(5)
    assert result is False
    assert mode.get_sensor_list() == [1, 2, 3]


def test_safehome_mode_delete_all_sensors():
    """Test deleting all sensors"""
    mode = SafeHomeMode(
        mode_id=1,
        mode_name="Home",
        sensor_ids=[1, 2, 3, 4, 5],
    )

    mode.delete_all_sensors()
    assert mode.get_sensor_list() == []


def test_safehome_mode_delete_all_sensors_already_empty():
    """Test deleting all sensors when list is already empty"""
    mode = SafeHomeMode(
        mode_id=1,
        mode_name="Home",
        sensor_ids=[],
    )

    mode.delete_all_sensors()
    assert mode.get_sensor_list() == []


def test_safehome_mode_str():
    """Test string representation"""
    mode = SafeHomeMode(
        mode_id=1,
        mode_name="Home",
        sensor_ids=[1, 2, 3, 4],
    )

    str_repr = str(mode)
    assert "ID=1" in str_repr
    assert "Mode='Home'" in str_repr
    assert "Sensors=4" in str_repr


def test_safehome_mode_str_empty_sensors():
    """Test string representation with empty sensor list"""
    mode = SafeHomeMode(
        mode_id=2,
        mode_name="Away",
        sensor_ids=[],
    )

    str_repr = str(mode)
    assert "ID=2" in str_repr
    assert "Mode='Away'" in str_repr
    assert "Sensors=0" in str_repr


def test_safehome_mode_to_schema():
    """Test conversion to SafeHomeModeSchema"""
    now = datetime.now()
    mode = SafeHomeMode(
        mode_id=1,
        mode_name="Home",
        sensor_ids=[1, 2, 3],
        created_at=now,
        updated_at=now,
    )

    schema = mode.to_schema()

    assert schema.mode_id == 1
    assert schema.mode_name == "Home"
    assert schema.sensor_ids == [1, 2, 3]
    assert schema.created_at == now


def test_safehome_mode_set_id_with_zero():
    """Test setting mode ID with zero"""
    mode = SafeHomeMode(
        mode_id=1,
        mode_name="Home",
        sensor_ids=[],
    )

    result = mode.set_id(0)
    assert result is True
    assert mode.get_id() == 0


def test_safehome_mode_set_id_with_negative():
    """Test setting mode ID with negative integer"""
    mode = SafeHomeMode(
        mode_id=1,
        mode_name="Home",
        sensor_ids=[],
    )

    result = mode.set_id(-5)
    assert result is True
    assert mode.get_id() == -5
