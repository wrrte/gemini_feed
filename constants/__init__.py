"""
Constants package for SafeHome system.
Provides centralized access to all system constants.
"""

# Import all constants from constant.py
# isort: off
from constants.constant import (
    FUNCTION_MODE_MESSAGE1,
    FUNCTION_MODE_MESSAGE2,
    MAX_LOGIN_TRIALS,
    PANEL_DEFAULT_MESSAGE1,
    PANEL_DEFAULT_MESSAGE2,
    PANEL_LOCK_TIME_SECONDS,
    PANEL_PASSWORD_LENGTH,
    UI_UPDATE_DELAY_MS,
    WEB_PASSWORD_LENGTH,
    COLOR_ARMED,
)
# isort: on

__all__ = [
    "MAX_LOGIN_TRIALS",
    "WEB_PASSWORD_LENGTH",
    "PANEL_PASSWORD_LENGTH",
    "UI_UPDATE_DELAY_MS",
    "PANEL_LOCK_TIME_SECONDS",
    "PANEL_DEFAULT_MESSAGE1",
    "PANEL_DEFAULT_MESSAGE2",
    "FUNCTION_MODE_MESSAGE1",
    "FUNCTION_MODE_MESSAGE2",
    "COLOR_ARMED",
]
