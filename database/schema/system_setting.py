from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SystemSettingSchema(BaseModel):
    system_setting_id: int
    panic_phone_number: Optional[str] = None
    homeowner_phone_number: Optional[str] = None
    system_lock_time: Optional[int] = None
    alarm_delay_time: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
