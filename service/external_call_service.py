class ExternalCallService:
    """
    External call service for SafeHome application.
    Implements singleton pattern to ensure single instance.
    Handles emergency calls to external phone numbers.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Singleton pattern - instance is reused
        # No initialization needed
        pass

    def call(self, phone_number: str) -> bool:
        """Make an external call to the specified phone number.

        Args:
            phone_number: Phone number to call

        Returns:
            bool: True if call was initiated successfully
        """
        # NOTE: Call is simulated with a print statement
        if (phone_number is None) or (phone_number == ""):
            return False
        print(f"Calling {phone_number}...")
        return True
