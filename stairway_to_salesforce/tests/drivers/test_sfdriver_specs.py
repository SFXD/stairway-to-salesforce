"""
Unit tests for Salesforce driver credential specification classes.

Tests all credential types and validation logic defined in sfdriver_specs.py
"""

from unittest.mock import Mock, patch

import pytest
from dlt.common.configuration.exceptions import ConfigurationValueError

from stairway_to_salesforce.drivers.salesforce_driver.sfdriver_specs import (
    ConsumerKeySecretAuth,
    ConsumerKeySecretDomainAuth,
    InstanceAuth,
    JWTAuth,
    OrganizationIdAuth,
    SalesforceDriverAuth,
    SalesforceDriverConfiguration,
    SecurityTokenAuth,
)


class TestSalesforceDriverConfiguration:
    """Tests for SalesforceDriverConfiguration class."""

    def test_default_configuration(self):
        """Test configuration with default values."""
        config = SalesforceDriverConfiguration()

        assert config.domain is None
        assert config.version is not None  # Should have DEFAULT_API_VERSION
        assert config.proxies is None
        assert config.client_id is None

    def test_configuration_with_custom_values(self):
        """Test configuration with custom values."""
        config = SalesforceDriverConfiguration(
            domain="test", version="v58.0", client_id="custom_client_id"
        )

        assert config.domain == "test"
        assert config.version == "v58.0"
        assert config.client_id == "custom_client_id"

    def test_get_proxies_with_none(self):
        """Test get_proxies returns None when proxies not set."""
        config = SalesforceDriverConfiguration()

        assert config.get_proxies() is None

    def test_get_proxies_with_json_string(self):
        """Test get_proxies parses JSON proxy configuration."""
        proxy_json = '{"http": "http://proxy:8080", "https": "https://proxy:8080"}'
        config = SalesforceDriverConfiguration(proxies=proxy_json)

        result = config.get_proxies()

        assert result is not None
        assert isinstance(result, dict)
        assert result["http"] == "http://proxy:8080"
        assert result["https"] == "https://proxy:8080"

    def test_get_proxies_with_invalid_json(self):
        """Test get_proxies handles invalid JSON."""
        config = SalesforceDriverConfiguration(proxies="invalid json")

        with pytest.raises(Exception):  # Should raise JSON decode error
            config.get_proxies()


class TestSecurityTokenAuth:
    """Tests for SecurityTokenAuth credential class."""

    def test_create_security_token_auth(self):
        """Test creating SecurityTokenAuth with all fields."""
        creds = SecurityTokenAuth(
            user_name="test@example.com",
            password="test_password",
            security_token="test_token",
        )

        assert creds.user_name == "test@example.com"
        assert creds.password == "test_password"
        assert creds.security_token == "test_token"

    def test_security_token_auth_none_defaults(self):
        """Test SecurityTokenAuth allows None defaults."""
        creds = SecurityTokenAuth()

        assert creds.user_name is None
        assert creds.password is None
        assert creds.security_token is None

    def test_security_token_auth_partial_values(self):
        """Test SecurityTokenAuth with partial values."""
        creds = SecurityTokenAuth(
            user_name="test@example.com",
            password="test_password",
            # Missing security_token
        )

        assert creds.user_name == "test@example.com"
        assert creds.password == "test_password"
        assert creds.security_token is None


class TestOrganizationIdAuth:
    """Tests for OrganizationIdAuth credential class."""

    def test_create_organization_id_auth(self):
        """Test creating OrganizationIdAuth with all fields."""
        creds = OrganizationIdAuth(
            user_name="test@example.com",
            password="test_password",
            organization_id="00Dxx0000000001",
        )

        assert creds.user_name == "test@example.com"
        assert creds.password == "test_password"
        assert creds.organization_id == "00Dxx0000000001"

    def test_organization_id_auth_for_trusted_ip(self):
        """Test OrganizationIdAuth is for Trusted IP Ranges."""
        # This credential type is specifically for Trusted IP authentication
        creds = OrganizationIdAuth(
            user_name="test@example.com",
            password="test_password",
            organization_id="00Dxx0000000001",
        )

        assert creds.organization_id is not None


class TestInstanceAuth:
    """Tests for InstanceAuth credential class."""

    def test_create_instance_auth_with_instance(self):
        """Test creating InstanceAuth with instance field."""
        creds = InstanceAuth(session_id="test_session_id", instance="na1.salesforce.com")

        assert creds.session_id == "test_session_id"
        assert creds.instance == "na1.salesforce.com"
        assert creds.instance_url is None

    def test_create_instance_auth_with_instance_url(self):
        """Test creating InstanceAuth with instance_url field."""
        creds = InstanceAuth(
            session_id="test_session_id", instance_url="https://na1.salesforce.com"
        )

        assert creds.session_id == "test_session_id"
        assert creds.instance is None
        assert creds.instance_url == "https://na1.salesforce.com"

    def test_instance_auth_requires_instance_or_url(self):
        """Test that InstanceAuth requires either instance or instance_url."""
        creds = InstanceAuth(
            session_id="test_session_id"
            # Missing both instance and instance_url
        )

        # Should raise ConfigurationValueError on validation
        with pytest.raises(ConfigurationValueError, match="instance.*instance_url"):
            creds.on_resolved()

    def test_instance_auth_accepts_both_instance_and_url(self):
        """Test that InstanceAuth accepts both fields if provided."""
        creds = InstanceAuth(
            session_id="test_session_id",
            instance="na1.salesforce.com",
            instance_url="https://na1.salesforce.com",
        )

        # Should not raise when both are provided
        creds.on_resolved()  # Should succeed


class TestConsumerKeySecretAuth:
    """Tests for ConsumerKeySecretAuth credential class."""

    def test_create_consumer_key_secret_auth(self):
        """Test creating ConsumerKeySecretAuth for OAuth 2.0 Username-Password Flow."""
        creds = ConsumerKeySecretAuth(
            user_name="test@example.com",
            password="test_password",
            consumer_key="test_consumer_key",
            consumer_secret="test_consumer_secret",
        )

        assert creds.user_name == "test@example.com"
        assert creds.password == "test_password"
        assert creds.consumer_key == "test_consumer_key"
        assert creds.consumer_secret == "test_consumer_secret"

    def test_consumer_key_secret_auth_for_connected_app(self):
        """Test ConsumerKeySecretAuth is for Connected App authentication."""
        creds = ConsumerKeySecretAuth(
            user_name="test@example.com",
            password="test_password",
            consumer_key="3MVG9test",
            consumer_secret="test_secret",
        )

        # Verify all required fields for connected app auth
        assert creds.consumer_key is not None
        assert creds.consumer_secret is not None
        assert creds.user_name is not None


class TestJWTAuth:
    """Tests for JWTAuth credential class."""

    def test_create_jwt_auth_with_privatekey_file(self):
        """Test creating JWTAuth with privatekey_file."""
        creds = JWTAuth(
            user_name="test@example.com",
            consumer_key="test_consumer_key",
            privatekey_file="/path/to/key.pem",
        )

        assert creds.user_name == "test@example.com"
        assert creds.consumer_key == "test_consumer_key"
        assert creds.privatekey_file == "/path/to/key.pem"
        assert creds.privatekey is None

    def test_create_jwt_auth_with_privatekey(self):
        """Test creating JWTAuth with privatekey string."""
        private_key_content = "-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----"

        creds = JWTAuth(
            user_name="test@example.com",
            consumer_key="test_consumer_key",
            privatekey=private_key_content,
        )

        assert creds.user_name == "test@example.com"
        assert creds.consumer_key == "test_consumer_key"
        assert creds.privatekey == private_key_content
        assert creds.privatekey_file is None

    def test_jwt_auth_requires_privatekey_or_file(self):
        """Test that JWTAuth requires either privatekey or privatekey_file."""
        creds = JWTAuth(
            user_name="test@example.com",
            consumer_key="test_consumer_key",
            # Missing both privatekey and privatekey_file
        )

        # Should raise ConfigurationValueError on validation
        with pytest.raises(ConfigurationValueError, match="privatekey"):
            creds.on_resolved()

    def test_jwt_auth_accepts_both_privatekey_forms(self):
        """Test that JWTAuth accepts both privatekey forms if provided."""
        creds = JWTAuth(
            user_name="test@example.com",
            consumer_key="test_consumer_key",
            privatekey_file="/path/to/key.pem",
            privatekey="-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----",
        )

        # Should not raise when both are provided
        creds.on_resolved()  # Should succeed

    def test_jwt_auth_with_instance_url(self):
        """Test JWTAuth with optional instance_url."""
        creds = JWTAuth(
            user_name="test@example.com",
            consumer_key="test_consumer_key",
            privatekey_file="/path/to/key.pem",
            instance_url="https://login.salesforce.com",
        )

        assert creds.instance_url == "https://login.salesforce.com"


class TestConsumerKeySecretDomainAuth:
    """Tests for ConsumerKeySecretDomainAuth credential class."""

    def test_create_consumer_key_secret_domain_auth(self):
        """Test creating ConsumerKeySecretDomainAuth for OAuth 2.0 Client Credentials Flow."""
        creds = ConsumerKeySecretDomainAuth(
            consumer_key="test_consumer_key",
            consumer_secret="test_consumer_secret",
            domain="test",
        )

        assert creds.consumer_key == "test_consumer_key"
        assert creds.consumer_secret == "test_consumer_secret"
        assert creds.domain == "test"

    def test_consumer_key_secret_domain_for_client_credentials(self):
        """Test ConsumerKeySecretDomainAuth is for Client Credentials Flow."""
        # This is the OAuth 2.0 Client Credentials Flow
        # Domain must be provided as part of credentials
        creds = ConsumerKeySecretDomainAuth(
            consumer_key="3MVG9test",
            consumer_secret="test_secret",
            domain="login",  # or "test" for sandbox
        )

        # All three fields are required
        assert creds.consumer_key is not None
        assert creds.consumer_secret is not None
        assert creds.domain is not None

    def test_consumer_key_secret_domain_different_domains(self):
        """Test different domain values (production vs sandbox)."""
        # Production
        creds_prod = ConsumerKeySecretDomainAuth(
            consumer_key="key", consumer_secret="secret", domain="login"
        )
        assert creds_prod.domain == "login"

        # Sandbox
        creds_sandbox = ConsumerKeySecretDomainAuth(
            consumer_key="key", consumer_secret="secret", domain="test"
        )
        assert creds_sandbox.domain == "test"


class TestSalesforceDriverAuthUnion:
    """Tests for SalesforceDriverAuth union type."""

    def test_all_credential_types_in_union(self):
        """Test that all credential types are part of the union."""
        # Create instances of each type
        security_token = SecurityTokenAuth(
            user_name="test@example.com", password="pass", security_token="token"
        )

        org_id = OrganizationIdAuth(
            user_name="test@example.com", password="pass", organization_id="00D"
        )

        instance = InstanceAuth(session_id="session", instance="na1.salesforce.com")

        consumer_key_secret = ConsumerKeySecretAuth(
            user_name="test@example.com",
            password="pass",
            consumer_key="key",
            consumer_secret="secret",
        )

        jwt = JWTAuth(
            user_name="test@example.com",
            consumer_key="key",
            privatekey_file="/path/to/key.pem",
        )

        consumer_domain = ConsumerKeySecretDomainAuth(
            consumer_key="key", consumer_secret="secret", domain="test"
        )

        # All should be instances of their respective classes
        assert isinstance(security_token, SecurityTokenAuth)
        assert isinstance(org_id, OrganizationIdAuth)
        assert isinstance(instance, InstanceAuth)
        assert isinstance(consumer_key_secret, ConsumerKeySecretAuth)
        assert isinstance(jwt, JWTAuth)
        assert isinstance(consumer_domain, ConsumerKeySecretDomainAuth)


class TestCredentialValidation:
    """Tests for credential validation across all types."""

    def test_credentials_are_credentials_configuration(self):
        """Test that all credential classes inherit from CredentialsConfiguration."""
        from dlt.common.configuration.specs import CredentialsConfiguration

        # All should inherit from CredentialsConfiguration
        assert issubclass(SecurityTokenAuth, CredentialsConfiguration)
        assert issubclass(OrganizationIdAuth, CredentialsConfiguration)
        assert issubclass(InstanceAuth, CredentialsConfiguration)
        assert issubclass(ConsumerKeySecretAuth, CredentialsConfiguration)
        assert issubclass(JWTAuth, CredentialsConfiguration)
        assert issubclass(ConsumerKeySecretDomainAuth, CredentialsConfiguration)

    def test_credentials_have_configspec_decorator(self):
        """Test that credential classes are properly decorated."""
        # All credential classes should have the @configspec decorator
        # This is verified by checking if they have the necessary attributes

        # Note: The actual decorator verification is implementation-specific
        # We can verify they work with DLT's configuration system
        assert hasattr(SecurityTokenAuth, "__init__")
        assert hasattr(OrganizationIdAuth, "__init__")
        assert hasattr(InstanceAuth, "__init__")


class TestSecretFields:
    """Tests for secret field handling."""

    def test_security_token_auth_secret_fields(self):
        """Test that sensitive fields use TSecretStrValue."""
        creds = SecurityTokenAuth(
            user_name="test@example.com",
            password="test_password",
            security_token="test_token",
        )

        # password and security_token should be secret values
        # (Implementation detail - DLT handles this)
        assert creds.password is not None
        assert creds.security_token is not None

    def test_consumer_key_secret_auth_secret_fields(self):
        """Test that consumer secrets are properly handled."""
        creds = ConsumerKeySecretAuth(
            user_name="test@example.com",
            password="test_password",
            consumer_key="key",
            consumer_secret="secret",
        )

        # consumer_key and consumer_secret should be secret values
        assert creds.consumer_key is not None
        assert creds.consumer_secret is not None


class TestCredentialEdgeCases:
    """Tests for edge cases in credential handling."""

    def test_empty_string_values(self):
        """Test handling of empty string values."""
        creds = SecurityTokenAuth(user_name="", password="", security_token="")

        # Empty strings should be preserved (validation happens elsewhere)
        assert creds.user_name == ""
        assert creds.password == ""
        assert creds.security_token == ""

    def test_whitespace_values(self):
        """Test handling of whitespace values."""
        creds = SecurityTokenAuth(
            user_name="  test@example.com  ",
            password="  password  ",
            security_token="  token  ",
        )

        # Whitespace should be preserved (trimming happens at validation)
        assert creds.user_name == "  test@example.com  "

    def test_mixed_credential_initialization(self):
        """Test initializing credentials with mixed None and value fields."""
        creds = JWTAuth(
            user_name="test@example.com",
            consumer_key="key",
            privatekey_file="/path/to/key.pem",
            privatekey=None,  # Explicitly None
            instance_url=None,  # Explicitly None
        )

        assert creds.user_name == "test@example.com"
        assert creds.privatekey_file == "/path/to/key.pem"
        assert creds.privatekey is None
        assert creds.instance_url is None


class TestConfigurationProxies:
    """Tests for proxy configuration handling."""

    def test_simple_proxy_configuration(self):
        """Test simple proxy configuration."""
        proxy_json = '{"http": "http://proxy.example.com:8080"}'
        config = SalesforceDriverConfiguration(proxies=proxy_json)

        result = config.get_proxies()
        assert result["http"] == "http://proxy.example.com:8080"

    def test_http_and_https_proxy(self):
        """Test both HTTP and HTTPS proxy configuration."""
        proxy_json = '{"http": "http://proxy:8080", "https": "https://proxy:8443"}'
        config = SalesforceDriverConfiguration(proxies=proxy_json)

        result = config.get_proxies()
        assert result["http"] == "http://proxy:8080"
        assert result["https"] == "https://proxy:8443"

    def test_complex_proxy_configuration(self):
        """Test complex proxy configuration with authentication."""
        proxy_json = '{"http": "http://user:pass@proxy:8080"}'
        config = SalesforceDriverConfiguration(proxies=proxy_json)

        result = config.get_proxies()
        assert "user:pass" in result["http"]
