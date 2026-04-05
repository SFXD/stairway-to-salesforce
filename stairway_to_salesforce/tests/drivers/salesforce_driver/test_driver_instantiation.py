from unittest.mock import Mock, patch
import pytest
from requests.exceptions import JSONDecodeError as RequestsJSONDecodeError
from stairway_to_salesforce.drivers.salesforce_driver.driver_builder import (
    make_salesforce_driver,
    _safe_instantiate
)
from stairway_to_salesforce.drivers.salesforce_driver.specs import SecurityTokenAuth

class TestDriverSecurity:
    """Tests focused on network robustness and safe instantiation."""

    @patch("stairway_to_salesforce.drivers.salesforce_driver.driver_builder.Salesforce")
    def test_safe_instantiate_handles_corrupt_response(self, mock_sf_class):
        """Checks if char 0 JSON errors are caught and re-raised cleanly."""
        mock_sf_class.side_effect = RequestsJSONDecodeError("Expecting value", "", 0)

        with pytest.raises(RuntimeError) as exc_info:
            _safe_instantiate({"username": "test"})
        assert "Invalid server response format" in str(exc_info.value)

class TestDriverParams:
    """Tests that parameters are correctly passed to simple-salesforce."""

    @patch("stairway_to_salesforce.drivers.salesforce_driver.driver_builder.Salesforce")
    def test_make_driver_passes_all_params(self, mock_sf_class):
        creds = SecurityTokenAuth(user_name="u", password="p", security_token="s")
        make_salesforce_driver(creds)

        args, kwargs = mock_sf_class.call_args
        assert kwargs["username"] == "u"
        assert kwargs["security_token"] == "s"
