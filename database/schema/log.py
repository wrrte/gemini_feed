from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogSchema(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    level: LogLevel = Field(default=LogLevel.INFO)
    message: str = Field(default="")
    filename: str = Field(default="")
    function_name: str = Field(default="")
    line_number: int = Field(default=0)
