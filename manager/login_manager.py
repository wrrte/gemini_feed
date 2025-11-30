from typing import Optional

# isort: off
from constants import (
    MAX_LOGIN_TRIALS,
    PANEL_PASSWORD_LENGTH,
    WEB_PASSWORD_LENGTH,
)
# isort: on

from manager.storage_manager import StorageManager


class LoginManager:
    def __init__(
        self,
        storage_manager: StorageManager,
    ) -> None:
        """
        Initialize the LoginManager.
        """
        self.storage_manager = storage_manager
        self.login_trials = 0
        self.current_user_id = None
        self.is_logged_in_web = False
        self.is_logged_in_panel = False

    def login_panel(
        self, panel_id: str, password: Optional[str] = None
    ) -> bool:
        """
        Authenticate user via control panel.

        Args:
            panel_id: Control panel user ID
            password: Control panel password

        Returns:
            bool: True if authentication successful
        """
        if self._verify_panel_password(panel_id, password):
            self.login_trials = 0
            self.current_user_id = panel_id
            self.is_logged_in_panel = True
            return True
        else:
            self.login_trials += 1
            self.is_logged_in_panel = False
            return False

    def logout_web(self):
        """
        Log out from web interface.
        """
        self.is_logged_in_web = False
        self.current_user_id = None
        self.login_trials = 0

    def login_web(self, user_id: str, password: str) -> bool:
        """
        Authenticate user via web interface.

        Args:
            user_id: Web user ID
            password: Web password

        Returns:
            bool: True if authentication successful
        """
        if self._verify_web_password(user_id, password):
            self.login_trials = 0
            self.current_user_id = user_id
            self.is_logged_in_web = True
            return True
        else:
            self.login_trials += 1
            self.is_logged_in_web = False
            return False

    def logout_panel(self):
        """
        Log out from control panel.
        """
        self.is_logged_in_panel = False
        self.current_user_id = None
        self.login_trials = 0

    def change_panel_password(
        self, panel_id: str, old_password: str, new_password: str
    ) -> bool:
        """
        Change control panel password.

        Args:
            panel_id: Control panel user ID
            old_password: Current password for verification
            new_password: New password to set

        Returns:
            bool: True if password changed successfully
        """
        if not self._verify_panel_password(panel_id, old_password):
            print("Old password is incorrect")
            return False

        # Validate new password
        if not self._validate_panel_password(new_password):
            print("New password does not meet requirements")
            return False

        # Update password in database
        try:
            result = self.storage_manager.execute_query(
                """UPDATE users SET panel_password = ?,
                updated_at = CURRENT_TIMESTAMP WHERE panel_id = ?""",
                (new_password, panel_id),
            )
            return result is not None
        except Exception as e:
            print(f"Failed to change panel password: {e}")
            return False

    def change_web_password(
        self, user_id: str, old_password: str, new_password: str
    ) -> bool:
        """
        Change web interface password.

        Args:
            user_id: Web user ID
            old_password: Current password for verification
            new_password: New password to set

        Returns:
            bool: True if password changed successfully
        """
        if not self._verify_web_password(user_id, old_password):
            print("Old password is incorrect")
            return False

        # Validate new password
        if not self._validate_web_password(new_password):
            print("New password does not meet requirements")
            return False

        # Update password in database
        try:
            result = self.storage_manager.execute_query(
                """UPDATE users SET web_password = ?,
                updated_at = CURRENT_TIMESTAMP WHERE web_id = ?""",
                (new_password, user_id),
            )
            return result is not None
        except Exception as e:
            print(f"Failed to change web password: {e}")
            return False

    def is_login_trials_exceeded(self) -> bool:
        """
        Check if login trials exceed the maximum allowed.
        """
        return self.login_trials >= MAX_LOGIN_TRIALS

    def _verify_panel_password(
        self, panel_id: str, password: Optional[str] = None
    ) -> bool:
        """
        Verify panel password without affecting login_trials.

        Args:
            panel_id: Control panel user ID
            password: Password to verify (None for users with no password)

        Returns:
            bool: True if password is correct
        """
        # Handle NULL password case (for guest with no password)
        if password is None:
            result = self.storage_manager.execute_query(
                "SELECT * FROM users WHERE panel_id = ? "
                "AND panel_password IS NULL",
                (panel_id,),
            )
        else:
            result = self.storage_manager.execute_query(
                "SELECT * FROM users WHERE panel_id = ? "
                "AND panel_password = ?",
                (panel_id, password),
            )
        return result is not None and len(result) > 0

    def _verify_web_password(self, user_id: str, password: str) -> bool:
        """
        Verify web password without affecting login_trials.

        Args:
            user_id: Web user ID
            password: Password to verify

        Returns:
            bool: True if password is correct
        """
        result = self.storage_manager.execute_query(
            "SELECT * FROM users WHERE web_id = ? AND web_password = ?",
            (user_id, password),
        )
        return result is not None and len(result) > 0

    def _validate_web_password(self, password: str) -> bool:
        """
        Validate if web password meets requirements (8 char).

        Args:
            password: Password to validate

        Returns:
            bool: True if password is valid
        """
        if not password or not isinstance(password, str):
            return False

        # Length requirement
        if len(password) != WEB_PASSWORD_LENGTH:
            return False

        return True

    def _validate_panel_password(self, password: str) -> bool:
        """
        Validate if web password meets requirements (4 digit number).

        Args:
            password: Password to validate

        Returns:
            bool: True if password is valid
        """
        if not password or not isinstance(password, str):
            return False

        if len(password) != PANEL_PASSWORD_LENGTH or not password.isdigit():
            return False

        return True
