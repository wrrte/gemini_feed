from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class CameraControlType(Enum):
    PAN_RIGHT = 0
    PAN_LEFT = 1
    ZOOM_IN = 2
    ZOOM_OUT = 3


class CameraValidationResult(Enum):
    VALID = 0
    NO_PASSWORD = 1
    INVALID_ID = 2
    INCORRECT = 3


class CameraSchema(BaseModel):
    camera_id: int
    coordinate_x: int
    coordinate_y: int
    pan: int
    zoom_setting: int
    has_password: bool
    password: Optional[str]
    enabled: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
