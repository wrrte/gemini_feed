from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class SensorType(Enum):
    WINDOOR_SENSOR = 1
    MOTION_DETECTOR_SENSOR = 2


class SensorSchema(BaseModel):
    sensor_id: int
    sensor_type: SensorType
    coordinate_x: int
    coordinate_y: int
    coordinate_x2: Optional[int] = None
    coordinate_y2: Optional[int] = None
    armed: bool = False
    created_at: datetime
    updated_at: datetime
