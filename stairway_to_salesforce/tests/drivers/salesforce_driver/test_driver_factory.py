from unittest.mock import Mock, patch
import pytest
from stairway_to_salesforce.drivers.salesforce_driver.driver_factory import get_sf_driver
from stairway_to_salesforce.drivers.salesforce_driver.specs import (
    SecurityTokenAuth,
    SalesforceDriverConfiguration,
)

class TestGetSalesforceDriver:
    def setup_method(self):
        from stairway_to_salesforce.drivers.salesforce_driver.driver_cache import clear_cache
        clear_cache()

    @patch("stairway_to_salesforce.drivers.salesforce_driver.driver_factory.make_salesforce_driver")
    @patch("dlt.secrets")
    def test_get_driver_with_string_credentials_uses_cache(self, mock_secrets, mock_make_driver):
        mock_driver = Mock()
        mock_make_driver.return_value = mock_driver
        mock_secrets.__getitem__.return_value = {"security_token": "token"}

        get_sf_driver("salesforce.test")
        get_sf_driver("salesforce.test")

        assert mock_make_driver.call_count == 1

    @patch("stairway_to_salesforce.drivers.salesforce_driver.driver_factory.make_salesforce_driver")
    @patch("dlt.secrets")
    def test_get_driver_unicode_path(self, mock_secrets, mock_make_driver):
        mock_driver = Mock()
        mock_make_driver.return_value = mock_driver
        mock_secrets.__getitem__.return_value = {"security_token": "token"}

        result = get_sf_driver("salesforce.日本語")
        assert result is mock_driver

    @patch("stairway_to_salesforce.drivers.salesforce_driver.driver_factory.make_salesforce_driver")
    def test_get_driver_with_direct_specs(self, mock_make_driver):
        mock_make_driver.return_value = Mock()
        creds = SecurityTokenAuth(user_name="u", password="p", security_token="s")

        get_sf_driver(creds)
        assert mock_make_driver.call_count == 1

    def test_get_sf_driver_invalid_type_final_else(self):
        expected_msg = "Invalid credentials type provided. Expected string, dict, or Salesforce Auth spec."
        with pytest.raises(ValueError, match=expected_msg):
            get_sf_driver(12345)
