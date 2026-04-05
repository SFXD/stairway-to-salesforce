from unittest.mock import Mock, patch
import pytest
from stairway_to_salesforce.drivers.salesforce_driver.driver_builder import (
    make_salesforce_driver,
    _safe_instantiate
)
from stairway_to_salesforce.drivers.salesforce_driver.specs import (
    SecurityTokenAuth,
    InstanceAuth,
    OrganizationIdAuth,
    ConsumerKeySecretAuth,
    JWTAuth,
    ConsumerKeySecretDomainAuth
)

class TestDriverBuilder:
    @patch("stairway_to_salesforce.drivers.salesforce_driver.driver_builder.Salesforce")
    def test_safe_instantiate_unexpected_error(self, mock_sf):
        mock_sf.side_effect = Exception("Boom")
        with pytest.raises(Exception, match="Boom"):
            _safe_instantiate({"param": "val"})

    @patch("stairway_to_salesforce.drivers.salesforce_driver.driver_builder.Salesforce")
    @pytest.mark.parametrize("auth_obj, expected_key", [
        (SecurityTokenAuth(security_token="s", user_name="u", password="p"), "security_token"),
        (InstanceAuth(session_id="s"), "session_id"),
        (OrganizationIdAuth(organization_id="o", user_name="u", password="p"), "organizationId"),
        (ConsumerKeySecretAuth(consumer_key="c", user_name="u", password="p"), "consumer_key"),
        (JWTAuth(consumer_key="c", privatekey="k", user_name="u"), "privatekey"),
        (ConsumerKeySecretDomainAuth(consumer_key="c", domain="d"), "domain"),
    ])
    def test_make_driver_all_auth_types(self, mock_sf, auth_obj, expected_key):
        make_salesforce_driver(auth_obj)
        call_kwargs = mock_sf.call_args[1]
        assert expected_key in call_kwargs

    @patch("stairway_to_salesforce.drivers.salesforce_driver.driver_builder.resolve_salesforce_credentials")
    def test_make_driver_unsupported_type(self, mock_resolve):
        """Forces an unknown object past the resolver to test builder's error branch."""
        mock_resolve.return_value = Mock() # On simule un objet résolu mais inconnu du builder
        with pytest.raises(ValueError, match="Unsupported credential type"):
            make_salesforce_driver("dummy_path")

    @patch("stairway_to_salesforce.drivers.salesforce_driver.driver_builder.Salesforce")
    def test_safe_instantiate_json_error(self, mock_sf):
        from requests.exceptions import JSONDecodeError
        mock_sf.side_effect = JSONDecodeError("msg", "", 0)

        with pytest.raises(RuntimeError, match="Invalid server response format"):
            _safe_instantiate({"param": "val"})
