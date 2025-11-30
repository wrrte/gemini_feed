from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SafetyZoneSchema(BaseModel):
    zone_id: Optional[int] = None
    zone_name: str
    coordinate_x1: float
    coordinate_y1: float
    coordinate_x2: float
    coordinate_y2: float
    arm_status: bool = False
    sensor_id_list: Optional[list[int]] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
