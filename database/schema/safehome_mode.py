from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SafeHomeModeSchema(BaseModel):
    mode_id: Optional[int] = None
    mode_name: str
    sensor_ids: list[int] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
