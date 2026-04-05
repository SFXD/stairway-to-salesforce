from unittest.mock import patch
import pytest
from stairway_to_salesforce.drivers.salesforce_driver.driver_resolver import (
    resolve_salesforce_credentials,
)
from stairway_to_salesforce.drivers.salesforce_driver.specs import (
    SecurityTokenAuth,
    OrganizationIdAuth,
    InstanceAuth,
    JWTAuth,
    ConsumerKeySecretDomainAuth,
    ConsumerKeySecretAuth,
)

class TestDriverResolver:
    def test_resolve_from_dict_security_token(self):
        data = {"security_token": "s", "user_name": "u", "password": "p"}
        res = resolve_salesforce_credentials(data)
        assert isinstance(res, SecurityTokenAuth)

    def test_resolve_from_dict_organization_id(self):
        data = {"organization_id": "o", "user_name": "u", "password": "p"}
        res = resolve_salesforce_credentials(data)
        assert isinstance(res, OrganizationIdAuth)

    def test_resolve_from_dict_instance_auth(self):
        data = {"session_id": "s", "instance_url": "i"}
        res = resolve_salesforce_credentials(data)
        assert isinstance(res, InstanceAuth)

    def test_resolve_from_dict_jwt_auth(self):
        data = {"privatekey": "k", "consumer_key": "c", "user_name": "u"}
        res = resolve_salesforce_credentials(data)
        assert isinstance(res, JWTAuth)

    def test_resolve_from_dict_client_credentials(self):
        data = {"domain": "d", "consumer_key": "c", "consumer_secret": "s"}
        res = resolve_salesforce_credentials(data)
        assert isinstance(res, ConsumerKeySecretDomainAuth)

    def test_resolve_from_dict_consumer_auth(self):
        data = {"consumer_key": "c", "consumer_secret": "s", "user_name": "u"}
        res = resolve_salesforce_credentials(data)
        assert isinstance(res, ConsumerKeySecretAuth)

    def test_resolve_invalid_dict_fields(self):
        """Couvre le raise ValueError de _resolve_from_dict."""
        with pytest.raises(ValueError, match="Could not determine Salesforce credential type"):
            resolve_salesforce_credentials({"unknown_field": "val"})

    def test_resolve_invalid_type_raises_error(self):
        msg = "Credentials must be a SalesforceDriverAuth instance, a dict, or a string."
        with pytest.raises(TypeError, match=msg):
            resolve_salesforce_credentials(123.45)

    @patch("dlt.secrets")
    def test_resolve_from_secrets_not_found(self, mock_secrets):
        mock_secrets.__getitem__.side_effect = KeyError()
        with pytest.raises(ValueError, match="Failed to load credentials from DLT path"):
            resolve_salesforce_credentials("missing.path")

    def test_resolve_with_existing_spec_object(self):
        creds = SecurityTokenAuth(user_name="u", password="p", security_token="s")
        res = resolve_salesforce_credentials(creds)
        assert res is creds
