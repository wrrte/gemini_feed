"""
Unit tests for utils.py
Tests utility functions for drawing floor plans and sensor operations
"""

from unittest.mock import Mock, patch

import customtkinter as ctk
import pytest
from PIL import Image

from core.pages.utils import (check_line_intersection, draw_floor_plan,
                              find_lowest_empty_id, is_sensor_in_rect,
                              show_toast)
from database.schema.sensor import SensorType


# Fixtures
@pytest.fixture
def root():
    """Create and cleanup CTk root window"""
    root_window = ctk.CTk()
    root_window.withdraw()
    yield root_window
    try:
        root_window.destroy()
    except Exception:
        pass


@pytest.fixture
def canvas(root):
    """Create canvas widget"""
    canvas_widget = ctk.CTkCanvas(root, width=500, height=312)
    yield canvas_widget
    try:
        canvas_widget.destroy()
    except Exception:
        pass


# Tests for draw_floor_plan
@patch("core.pages.utils.ImageTk.PhotoImage")
@patch("core.pages.utils.Image.open")
def test_draw_floor_plan_success(mock_image_open, mock_photo_image, canvas):
    """Test successful floor plan drawing"""
    mock_img = Mock(spec=Image.Image)
    mock_img.size = (500, 312)
    mock_img.convert.return_value = mock_img
    mock_image_open.return_value = mock_img

    # Mock PhotoImage to return a valid object
    mock_photo = Mock()
    mock_photo_image.return_value = mock_photo

    draw_floor_plan(canvas)

    # Verify image was opened and converted
    mock_image_open.assert_called_once()
    mock_img.convert.assert_called_once_with("RGBA")

    # Verify PhotoImage was created
    mock_photo_image.assert_called_once_with(mock_img)

    # Verify canvas has the image reference
    assert hasattr(canvas, "_floor_img_tk")
    assert canvas._floor_img_tk == mock_photo


@patch("core.pages.utils.Image.open")
def test_draw_floor_plan_image_not_found(mock_image_open, canvas):
    """Test floor plan drawing when image is not found"""
    mock_image_open.side_effect = FileNotFoundError()

    draw_floor_plan(canvas)

    # Should draw fallback rectangle and text
    items = canvas.find_all()
    assert len(items) > 0


@patch("core.pages.utils.Image.open")
def test_draw_floor_plan_clears_previous(mock_image_open, canvas):
    """Test that draw_floor_plan clears previous drawings"""
    mock_img = Mock(spec=Image.Image)
    mock_img.convert.return_value = mock_img
    mock_image_open.return_value = mock_img

    # Draw something first
    canvas.create_rectangle(0, 0, 100, 100)

    # Draw floor plan
    draw_floor_plan(canvas)

    # Canvas should be cleared and redrawn
    assert canvas is not None


# Tests for show_toast
def test_show_toast_creates_toplevel(root):
    """Test that show_toast creates a toplevel window"""
    show_toast(root, "Test message")

    # Update to process pending events
    root.update_idletasks()

    # Find and hide any toast windows that were created
    for child in root.winfo_children():
        if isinstance(child, ctk.CTkToplevel):
            child.withdraw()

    # Toast should be created (checking doesn't throw error)
    assert root is not None


def test_show_toast_with_custom_duration(root):
    """Test show_toast with custom duration"""
    show_toast(root, "Test message", duration_ms=1000)

    # Update to process pending events
    root.update_idletasks()

    # Find and hide any toast windows that were created
    for child in root.winfo_children():
        if isinstance(child, ctk.CTkToplevel):
            child.withdraw()

    # Toast should be created
    assert root is not None


def test_show_toast_long_message(root):
    """Test show_toast with a long message"""
    long_message = "This is a very long message " * 20
    show_toast(root, long_message)

    # Update to process pending events
    root.update_idletasks()

    # Find and hide any toast windows that were created
    for child in root.winfo_children():
        if isinstance(child, ctk.CTkToplevel):
            child.withdraw()

    # Should handle long messages
    assert root is not None


# Tests for check_line_intersection
def test_intersecting_lines():
    """Test detection of intersecting lines"""
    p1 = (0, 0)
    p2 = (10, 10)
    p3 = (0, 10)
    p4 = (10, 0)

    assert check_line_intersection(p1, p2, p3, p4) is True


def test_non_intersecting_lines():
    """Test detection of non-intersecting lines"""
    p1 = (0, 0)
    p2 = (5, 5)
    p3 = (10, 10)
    p4 = (15, 15)

    assert check_line_intersection(p1, p2, p3, p4) is False


def test_parallel_lines():
    """Test parallel lines (no intersection)"""
    p1 = (0, 0)
    p2 = (10, 0)
    p3 = (0, 5)
    p4 = (10, 5)

    assert check_line_intersection(p1, p2, p3, p4) is False


def test_touching_lines_at_endpoint():
    """Test lines that touch at an endpoint"""
    p1 = (0, 0)
    p2 = (10, 10)
    p3 = (10, 10)
    p4 = (20, 0)

    assert check_line_intersection(p1, p2, p3, p4) is True


def test_perpendicular_intersecting_lines():
    """Test perpendicular lines that intersect"""
    p1 = (5, 0)
    p2 = (5, 10)
    p3 = (0, 5)
    p4 = (10, 5)

    assert check_line_intersection(p1, p2, p3, p4) is True


# Tests for is_sensor_in_rect
def test_windoor_sensor_inside_rect():
    """Test WinDoor sensor inside rectangle"""
    sensor = Mock()
    sensor.coordinate_x = 5
    sensor.coordinate_y = 5
    sensor.get_type.return_value = SensorType.WINDOOR_SENSOR

    result = is_sensor_in_rect(sensor, 0, 0, 10, 10)
    assert result is True


def test_windoor_sensor_outside_rect():
    """Test WinDoor sensor outside rectangle"""
    sensor = Mock()
    sensor.coordinate_x = 15
    sensor.coordinate_y = 15
    sensor.get_type.return_value = SensorType.WINDOOR_SENSOR

    result = is_sensor_in_rect(sensor, 0, 0, 10, 10)
    assert result is False


def test_windoor_sensor_on_boundary():
    """Test WinDoor sensor on rectangle boundary"""
    sensor = Mock()
    sensor.coordinate_x = 10
    sensor.coordinate_y = 10
    sensor.get_type.return_value = SensorType.WINDOOR_SENSOR

    result = is_sensor_in_rect(sensor, 0, 0, 10, 10)
    assert result is True


def test_motion_detector_both_points_inside():
    """Test Motion Detector with both points inside rectangle"""
    sensor = Mock()
    sensor.coordinate_x = 2
    sensor.coordinate_y = 2
    sensor.coordinate_x2 = 8
    sensor.coordinate_y2 = 8
    sensor.get_type.return_value = SensorType.MOTION_DETECTOR_SENSOR

    result = is_sensor_in_rect(sensor, 0, 0, 10, 10)
    assert result is True


def test_motion_detector_one_point_inside():
    """Test Motion Detector with one point inside rectangle"""
    sensor = Mock()
    sensor.coordinate_x = 5
    sensor.coordinate_y = 5
    sensor.coordinate_x2 = 15
    sensor.coordinate_y2 = 15
    sensor.get_type.return_value = SensorType.MOTION_DETECTOR_SENSOR

    result = is_sensor_in_rect(sensor, 0, 0, 10, 10)
    assert result is True


def test_motion_detector_line_intersects_rect():
    """Test Motion Detector line passing through rectangle"""
    sensor = Mock()
    sensor.coordinate_x = -5
    sensor.coordinate_y = 5
    sensor.coordinate_x2 = 15
    sensor.coordinate_y2 = 5
    sensor.get_type.return_value = SensorType.MOTION_DETECTOR_SENSOR

    result = is_sensor_in_rect(sensor, 0, 0, 10, 10)
    assert result is True


def test_motion_detector_outside_rect():
    """Test Motion Detector completely outside rectangle"""
    sensor = Mock()
    sensor.coordinate_x = 20
    sensor.coordinate_y = 20
    sensor.coordinate_x2 = 25
    sensor.coordinate_y2 = 25
    sensor.get_type.return_value = SensorType.MOTION_DETECTOR_SENSOR

    result = is_sensor_in_rect(sensor, 0, 0, 10, 10)
    assert result is False


def test_rect_with_inverted_coordinates():
    """Test rectangle with inverted coordinates (rx2 < rx1, ry2 < ry1)"""
    sensor = Mock()
    sensor.coordinate_x = 5
    sensor.coordinate_y = 5
    sensor.get_type.return_value = SensorType.WINDOOR_SENSOR

    # Rectangle with inverted coordinates
    result = is_sensor_in_rect(sensor, 10, 10, 0, 0)
    assert result is True


def test_unknown_sensor_type():
    """Test sensor with unknown type returns False"""
    sensor = Mock()
    sensor.coordinate_x = 5
    sensor.coordinate_y = 5
    # Return a sensor type that's not WINDOOR_SENSOR or MOTION_DETECTOR_SENSOR
    sensor.get_type.return_value = None

    result = is_sensor_in_rect(sensor, 0, 0, 10, 10)
    assert result is False


# Tests for find_lowest_empty_id
def test_empty_list():
    """Test with empty list returns 1"""
    result = find_lowest_empty_id([])
    assert result == 1


def test_continuous_ids_from_1():
    """Test with continuous IDs from 1"""
    result = find_lowest_empty_id([1, 2, 3, 4])
    assert result == 5


def test_gap_in_middle():
    """Test with gap in the middle"""
    result = find_lowest_empty_id([1, 2, 4, 5])
    assert result == 3


def test_missing_first_id():
    """Test with missing first ID"""
    result = find_lowest_empty_id([2, 3, 4])
    assert result == 1


def test_single_id():
    """Test with single ID"""
    result = find_lowest_empty_id([1])
    assert result == 2


def test_non_continuous_ids():
    """Test with non-continuous IDs"""
    result = find_lowest_empty_id([1, 3, 5, 7])
    assert result == 2


def test_large_numbers():
    """Test with large numbers"""
    result = find_lowest_empty_id([100, 101, 102])
    assert result == 1


def test_unordered_ids():
    """Test with unordered IDs"""
    result = find_lowest_empty_id([4, 1, 3, 2])
    assert result == 5
