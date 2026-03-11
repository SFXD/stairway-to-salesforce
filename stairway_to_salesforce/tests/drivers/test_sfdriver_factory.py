"""
Unit tests for Salesforce driver factory.

Tests credential resolution and driver creation logic.
"""

from unittest.mock import Mock, patch

import pytest

from stairway_to_salesforce.drivers.salesforce_driver.sfdriver_factory import (
    make_salesforce_driver,
    resolve_salesforce_credentials,
)
from stairway_to_salesforce.drivers.salesforce_driver.sfdriver_specs import (
    ConsumerKeySecretAuth,
    ConsumerKeySecretDomainAuth,
    InstanceAuth,
    JWTAuth,
    OrganizationIdAuth,
    SalesforceDriverConfiguration,
    SecurityTokenAuth,
)


class TestResolveSalesforceCredentials:
    """Tests for resolve_salesforce_credentials() function."""

    def test_resolve_already_resolved_security_token(self):
        """Test that already resolved SecurityTokenAuth is returned as-is."""
        creds = SecurityTokenAuth(
            user_name="test@example.com",
            password="test_password",
            security_token="test_token",
        )

        result = resolve_salesforce_credentials(creds)

        assert result is creds
        assert isinstance(result, SecurityTokenAuth)

    def test_resolve_already_resolved_organization_id(self):
        """Test that already resolved OrganizationIdAuth is returned as-is."""
        creds = OrganizationIdAuth(
            user_name="test@example.com",
            password="test_password",
            organization_id="00Dxx0000000001",
        )

        result = resolve_salesforce_credentials(creds)

        assert result is creds
        assert isinstance(result, OrganizationIdAuth)

    def test_resolve_already_resolved_instance(self):
        """Test that already resolved InstanceAuth is returned as-is."""
        creds = InstanceAuth(session_id="test_session", instance="na1.salesforce.com")

        result = resolve_salesforce_credentials(creds)

        assert result is creds
        assert isinstance(result, InstanceAuth)

    def test_resolve_from_dict_security_token(self):
        """Test resolution from dict to SecurityTokenAuth."""
        cred_dict = {
            "user_name": "test@example.com",
            "password": "test_password",
            "security_token": "test_token",
        }

        result = resolve_salesforce_credentials(cred_dict)

        assert isinstance(result, SecurityTokenAuth)
        assert result.user_name == "test@example.com"
        assert result.password == "test_password"
        assert result.security_token == "test_token"

    def test_resolve_from_dict_organization_id(self):
        """Test resolution from dict to OrganizationIdAuth."""
        cred_dict = {
            "user_name": "test@example.com",
            "password": "test_password",
            "organization_id": "00Dxx0000000001",
        }

        result = resolve_salesforce_credentials(cred_dict)

        assert isinstance(result, OrganizationIdAuth)
        assert result.user_name == "test@example.com"
        assert result.organization_id == "00Dxx0000000001"

    def test_resolve_from_dict_instance_auth(self):
        """Test resolution from dict to InstanceAuth."""
        cred_dict = {"session_id": "test_session", "instance": "na1.salesforce.com"}

        result = resolve_salesforce_credentials(cred_dict)

        assert isinstance(result, InstanceAuth)
        assert result.session_id == "test_session"
        assert result.instance == "na1.salesforce.com"

    def test_resolve_from_dict_jwt_with_privatekey(self):
        """Test resolution from dict to JWTAuth with privatekey."""
        cred_dict = {
            "user_name": "test@example.com",
            "consumer_key": "test_key",
            "privatekey": "-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----",
        }

        result = resolve_salesforce_credentials(cred_dict)

        assert isinstance(result, JWTAuth)
        assert result.user_name == "test@example.com"
        assert result.consumer_key == "test_key"
        assert result.privatekey is not None

    def test_resolve_from_dict_jwt_with_privatekey_file(self):
        """Test resolution from dict to JWTAuth with privatekey_file."""
        cred_dict = {
            "user_name": "test@example.com",
            "consumer_key": "test_key",
            "privatekey_file": "/path/to/key.pem",
        }

        result = resolve_salesforce_credentials(cred_dict)

        assert isinstance(result, JWTAuth)
        assert result.privatekey_file == "/path/to/key.pem"

    def test_resolve_from_dict_consumer_key_secret_domain(self):
        """Test resolution from dict to ConsumerKeySecretDomainAuth."""
        cred_dict = {
            "consumer_key": "test_key",
            "consumer_secret": "test_secret",
            "domain": "test",
        }

        result = resolve_salesforce_credentials(cred_dict)

        assert isinstance(result, ConsumerKeySecretDomainAuth)
        assert result.consumer_key == "test_key"
        assert result.consumer_secret == "test_secret"
        assert result.domain == "test"

    def test_resolve_from_dict_consumer_key_secret_with_username(self):
        """Test resolution from dict to ConsumerKeySecretAuth."""
        cred_dict = {
            "user_name": "test@example.com",
            "password": "test_password",
            "consumer_key": "test_key",
            "consumer_secret": "test_secret",
        }

        result = resolve_salesforce_credentials(cred_dict)

        assert isinstance(result, ConsumerKeySecretAuth)
        assert result.user_name == "test@example.com"
        assert result.consumer_key == "test_key"

    @patch("dlt.secrets")
    def test_resolve_from_dlt_secrets_path(self, mock_secrets):
        """Test resolution from DLT secrets path string."""
        mock_creds_dict = {
            "user_name": "test@example.com",
            "password": "test_password",
            "security_token": "test_token",
        }

        # Mock dlt.secrets dictionary access
        mock_secrets.__getitem__.return_value = mock_creds_dict

        result = resolve_salesforce_credentials("salesforce.dev")

        assert isinstance(result, SecurityTokenAuth)
        mock_secrets.__getitem__.assert_called_once_with("salesforce.dev")

    @patch("dlt.secrets")
    def test_resolve_from_dlt_secrets_nested_path(self, mock_secrets):
        """Test resolution from nested DLT secrets path."""
        mock_creds_dict = {
            "consumer_key": "key",
            "consumer_secret": "secret",
            "domain": "test",
        }

        mock_secrets.__getitem__.return_value = mock_creds_dict

        result = resolve_salesforce_credentials("salesforce.sandbox.credentials")

        assert isinstance(result, ConsumerKeySecretDomainAuth)
        mock_secrets.__getitem__.assert_called_once_with("salesforce.sandbox.credentials")

    def test_resolve_invalid_dict_raises_error(self):
        """Test that invalid dict raises ValueError."""
        cred_dict = {"invalid_field": "value", "another_invalid": "value"}

        with pytest.raises(ValueError, match="Could not determine Salesforce credential type"):
            resolve_salesforce_credentials(cred_dict)

    def test_resolve_empty_dict_raises_error(self):
        """Test that empty dict raises ValueError."""
        with pytest.raises(ValueError, match="Could not determine Salesforce credential type"):
            resolve_salesforce_credentials({})

    def test_resolve_invalid_type_raises_error(self):
        """Test that invalid type raises TypeError."""
        with pytest.raises(TypeError, match="must be a SalesforceDriverAuth instance"):
            resolve_salesforce_credentials(123)

        with pytest.raises(TypeError, match="must be a SalesforceDriverAuth instance"):
            resolve_salesforce_credentials(["list", "of", "values"])

        with pytest.raises(TypeError, match="must be a SalesforceDriverAuth instance"):
            resolve_salesforce_credentials(None)

    @patch("dlt.secrets")
    def test_resolve_from_secrets_path_loading_error(self, mock_secrets):
        """Test error handling when loading from DLT secrets fails."""
        mock_secrets.__getitem__.side_effect = KeyError("Secret not found")

        with pytest.raises(ValueError, match="Failed to load credentials from DLT secrets path"):
            resolve_salesforce_credentials("salesforce.nonexistent")


class TestCredentialResolutionPriority:
    """Tests for credential type resolution priority order."""

    def test_security_token_takes_priority(self):
        """Test that security_token presence triggers SecurityTokenAuth."""
        # Even with other fields present, security_token should win
        cred_dict = {
            "user_name": "test@example.com",
            "password": "test_password",
            "security_token": "test_token",
            "organization_id": "00D",  # Also present
        }

        result = resolve_salesforce_credentials(cred_dict)

        # Should be SecurityTokenAuth, not OrganizationIdAuth
        assert isinstance(result, SecurityTokenAuth)

    def test_organization_id_priority_over_consumer_key(self):
        """Test that organization_id takes priority over consumer_key."""
        cred_dict = {
            "user_name": "test@example.com",
            "password": "test_password",
            "organization_id": "00D",
            "consumer_key": "key",
            "consumer_secret": "secret",
        }

        result = resolve_salesforce_credentials(cred_dict)

        assert isinstance(result, OrganizationIdAuth)

    def test_session_id_triggers_instance_auth(self):
        """Test that session_id presence triggers InstanceAuth."""
        cred_dict = {
            "session_id": "session",
            "instance": "na1.salesforce.com",
            "user_name": "test@example.com",  # Also present
            "password": "password",
        }

        result = resolve_salesforce_credentials(cred_dict)

        assert isinstance(result, InstanceAuth)

    def test_privatekey_triggers_jwt_auth(self):
        """Test that privatekey triggers JWTAuth."""
        cred_dict = {
            "user_name": "test@example.com",
            "consumer_key": "key",
            "privatekey": "-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----",
            "password": "password",  # Also present
        }

        result = resolve_salesforce_credentials(cred_dict)

        assert isinstance(result, JWTAuth)

    def test_domain_with_consumer_triggers_domain_auth(self):
        """Test that domain + consumer_key + consumer_secret triggers ConsumerKeySecretDomainAuth."""  # noqa: E501
        cred_dict = {
            "consumer_key": "key",
            "consumer_secret": "secret",
            "domain": "test",
        }

        result = resolve_salesforce_credentials(cred_dict)

        assert isinstance(result, ConsumerKeySecretDomainAuth)

    def test_consumer_key_secret_with_username(self):
        """Test ConsumerKeySecretAuth when username present."""
        cred_dict = {
            "user_name": "test@example.com",
            "password": "password",
            "consumer_key": "key",
            "consumer_secret": "secret",
            # No domain
        }

        result = resolve_salesforce_credentials(cred_dict)

        assert isinstance(result, ConsumerKeySecretAuth)


class TestMakeSalesforceDriver:
    """Tests for make_salesforce_driver() function."""

    @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver_factory.Salesforce")
    def test_make_driver_security_token_auth(self, mock_sf_class):
        """Test driver creation with SecurityTokenAuth."""
        mock_sf_instance = Mock()
        mock_sf_class.return_value = mock_sf_instance

        creds = SecurityTokenAuth(
            user_name="test@example.com",
            password="test_password",
            security_token="test_token",
        )
        config = SalesforceDriverConfiguration()

        result = make_salesforce_driver(creds, session=None, config=config)

        assert result == mock_sf_instance

        # Verify Salesforce was called with correct parameters
        call_kwargs = mock_sf_class.call_args[1]
        assert call_kwargs["username"] == "test@example.com"
        assert call_kwargs["password"] == "test_password"
        assert call_kwargs["security_token"] == "test_token"
        assert "version" in call_kwargs
        assert "domain" in call_kwargs

    @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver_factory.Salesforce")
    def test_make_driver_organization_id_auth(self, mock_sf_class):
        """Test driver creation with OrganizationIdAuth."""
        mock_sf_instance = Mock()
        mock_sf_class.return_value = mock_sf_instance

        creds = OrganizationIdAuth(
            user_name="test@example.com",
            password="test_password",
            organization_id="00Dxx0000000001",
        )
        config = SalesforceDriverConfiguration()

        result = make_salesforce_driver(creds, session=None, config=config)

        assert result == mock_sf_instance

        call_kwargs = mock_sf_class.call_args[1]
        assert call_kwargs["username"] == "test@example.com"
        assert call_kwargs["organizationId"] == "00Dxx0000000001"

    @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver_factory.Salesforce")
    def test_make_driver_instance_auth(self, mock_sf_class):
        """Test driver creation with InstanceAuth."""
        mock_sf_instance = Mock()
        mock_sf_class.return_value = mock_sf_instance

        creds = InstanceAuth(session_id="test_session", instance="na1.salesforce.com")
        config = SalesforceDriverConfiguration()

        result = make_salesforce_driver(creds, session=None, config=config)

        assert result == mock_sf_instance

        call_kwargs = mock_sf_class.call_args[1]
        assert call_kwargs["session_id"] == "test_session"
        assert call_kwargs["instance"] == "na1.salesforce.com"

    @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver_factory.Salesforce")
    def test_make_driver_consumer_key_secret_auth(self, mock_sf_class):
        """Test driver creation with ConsumerKeySecretAuth."""
        mock_sf_instance = Mock()
        mock_sf_class.return_value = mock_sf_instance

        creds = ConsumerKeySecretAuth(
            user_name="test@example.com",
            password="test_password",
            consumer_key="test_key",
            consumer_secret="test_secret",
        )
        config = SalesforceDriverConfiguration()

        result = make_salesforce_driver(creds, session=None, config=config)

        assert result == mock_sf_instance

        call_kwargs = mock_sf_class.call_args[1]
        assert call_kwargs["username"] == "test@example.com"
        assert call_kwargs["consumer_key"] == "test_key"
        assert call_kwargs["consumer_secret"] == "test_secret"

    @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver_factory.Salesforce")
    def test_make_driver_jwt_auth(self, mock_sf_class):
        """Test driver creation with JWTAuth."""
        mock_sf_instance = Mock()
        mock_sf_class.return_value = mock_sf_instance

        creds = JWTAuth(
            user_name="test@example.com",
            consumer_key="test_key",
            privatekey_file="/path/to/key.pem",
        )
        config = SalesforceDriverConfiguration()

        result = make_salesforce_driver(creds, session=None, config=config)

        assert result == mock_sf_instance

        call_kwargs = mock_sf_class.call_args[1]
        assert call_kwargs["username"] == "test@example.com"
        assert call_kwargs["consumer_key"] == "test_key"
        assert call_kwargs["privatekey_file"] == "/path/to/key.pem"

    @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver_factory.Salesforce")
    def test_make_driver_consumer_key_secret_domain_auth(self, mock_sf_class):
        """Test driver creation with ConsumerKeySecretDomainAuth."""
        mock_sf_instance = Mock()
        mock_sf_class.return_value = mock_sf_instance

        creds = ConsumerKeySecretDomainAuth(
            consumer_key="test_key", consumer_secret="test_secret", domain="test"
        )
        config = SalesforceDriverConfiguration()

        result = make_salesforce_driver(creds, session=None, config=config)

        assert result == mock_sf_instance

        call_kwargs = mock_sf_class.call_args[1]
        assert call_kwargs["consumer_key"] == "test_key"
        assert call_kwargs["consumer_secret"] == "test_secret"
        assert call_kwargs["domain"] == "test"

    @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver_factory.Salesforce")
    def test_make_driver_resolves_dict_credentials(self, mock_sf_class):
        """Test that make_salesforce_driver resolves dict credentials."""
        mock_sf_instance = Mock()
        mock_sf_class.return_value = mock_sf_instance

        cred_dict = {
            "user_name": "test@example.com",
            "password": "test_password",
            "security_token": "test_token",
        }
        config = SalesforceDriverConfiguration()

        result = make_salesforce_driver(cred_dict, session=None, config=config)

        assert result == mock_sf_instance
        # Should have resolved to SecurityTokenAuth and called Salesforce()
        mock_sf_class.assert_called_once()

    @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver_factory.Salesforce")
    def test_make_driver_with_custom_session(self, mock_sf_class):
        """Test driver creation with custom session."""
        mock_sf_instance = Mock()
        mock_sf_class.return_value = mock_sf_instance
        mock_session = Mock()

        creds = SecurityTokenAuth(
            user_name="test@example.com",
            password="test_password",
            security_token="test_token",
        )
        config = SalesforceDriverConfiguration()

        result = make_salesforce_driver(creds, session=mock_session, config=config)

        assert result == mock_sf_instance

        call_kwargs = mock_sf_class.call_args[1]
        assert call_kwargs["session"] == mock_session

    @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver_factory.Salesforce")
    def test_make_driver_with_custom_config(self, mock_sf_class):
        """Test driver creation with custom configuration."""
        mock_sf_instance = Mock()
        mock_sf_class.return_value = mock_sf_instance

        creds = SecurityTokenAuth(
            user_name="test@example.com",
            password="test_password",
            security_token="test_token",
        )
        config = SalesforceDriverConfiguration(
            version="v58.0", domain="test", client_id="custom_client"
        )

        result = make_salesforce_driver(creds, session=None, config=config)

        assert result == mock_sf_instance

        call_kwargs = mock_sf_class.call_args[1]
        assert call_kwargs["version"] == "v58.0"
        assert call_kwargs["domain"] == "test"
        assert call_kwargs["client_id"] == "custom_client"

    @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver_factory.Salesforce")
    def test_make_driver_with_proxies(self, mock_sf_class):
        """Test driver creation with proxy configuration."""
        mock_sf_instance = Mock()
        mock_sf_class.return_value = mock_sf_instance

        creds = SecurityTokenAuth(
            user_name="test@example.com",
            password="test_password",
            security_token="test_token",
        )

        proxy_json = '{"http": "http://proxy:8080", "https": "https://proxy:8080"}'
        config = SalesforceDriverConfiguration(proxies=proxy_json)

        result = make_salesforce_driver(creds, session=None, config=config)

        assert result == mock_sf_instance

        call_kwargs = mock_sf_class.call_args[1]
        assert "proxies" in call_kwargs
        assert call_kwargs["proxies"] is not None


class TestDriverFactoryEdgeCases:
    """Tests for edge cases in driver factory."""

    @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver_factory.Salesforce")
    def test_make_driver_preserves_credential_fields(self, mock_sf_class):
        """Test that all credential fields are passed to Salesforce()."""
        mock_sf_instance = Mock()
        mock_sf_class.return_value = mock_sf_instance

        creds = SecurityTokenAuth(
            user_name="test@example.com",
            password="test_password",
            security_token="test_token",
        )
        config = SalesforceDriverConfiguration()

        make_salesforce_driver(creds, session=None, config=config)

        # Verify all SecurityTokenAuth fields passed
        call_kwargs = mock_sf_class.call_args[1]
        assert call_kwargs["username"] == "test@example.com"
        assert call_kwargs["password"] == "test_password"
        assert call_kwargs["security_token"] == "test_token"

    def test_resolve_credentials_error_message_quality(self):
        """Test that error messages provide helpful guidance."""
        cred_dict = {"random_field": "value"}

        with pytest.raises(ValueError) as exc_info:
            resolve_salesforce_credentials(cred_dict)

        error_msg = str(exc_info.value)
        # Should mention supported credential types
        assert "SecurityTokenAuth" in error_msg or "credential type" in error_msg
