from enum import Enum
from typing import Optional

from pydantic import BaseModel


class UserRole(str, Enum):
    HOMEOWNER = "HOMEOWNER"
    GUEST = "GUEST"


class User(BaseModel):
    user_id: str
    role: UserRole
    panel_id: str
    panel_password: Optional[str]
    web_id: Optional[str] = None
    web_password: Optional[str] = None
