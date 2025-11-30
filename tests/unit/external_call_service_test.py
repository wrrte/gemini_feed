from unittest.mock import patch

from service.external_call_service import ExternalCallService


def test_external_call_service_singleton():
    """Test that ExternalCallService follows singleton pattern"""
    service1 = ExternalCallService()
    service2 = ExternalCallService()

    assert service1 is service2


def test_external_call_service_initialization():
    """Test ExternalCallService initialization"""
    service = ExternalCallService()

    assert service is not None
    assert isinstance(service, ExternalCallService)


def test_external_call_service_call_with_valid_phone_number():
    """Test call method with valid phone number"""
    service = ExternalCallService()

    with patch("builtins.print") as mock_print:
        result = service.call("911")

        assert result is True
        mock_print.assert_called_once_with("Calling 911...")


def test_external_call_service_call_with_empty_string():
    """Test call method with empty string returns False"""
    service = ExternalCallService()

    with patch("builtins.print") as mock_print:
        result = service.call("")

        assert result is False
        mock_print.assert_not_called()


def test_external_call_service_call_with_none():
    """Test call method with None returns False"""
    service = ExternalCallService()

    with patch("builtins.print") as mock_print:
        result = service.call(None)

        assert result is False
        mock_print.assert_not_called()
