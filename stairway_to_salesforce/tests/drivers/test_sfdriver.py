"""
Unit tests for main Salesforce driver module (get_salesforce_driver).

Tests the public API and integration of cache, factory, and configuration.
"""

from unittest.mock import Mock, patch

import pytest

from stairway_to_salesforce.drivers.salesforce_driver.sfdriver import get_salesforce_driver
from stairway_to_salesforce.drivers.salesforce_driver.sfdriver_specs import (
    ConsumerKeySecretDomainAuth,
    SalesforceDriverAuth,
    SalesforceDriverConfiguration,
    SecurityTokenAuth,
)


class TestGetSalesforceDriver:
    """Tests for get_salesforce_driver() public API."""

    def setup_method(self):
        """Clear cache before each test."""
        from stairway_to_salesforce.drivers.salesforce_driver.sfdriver_cache_manager import (
            clear_cache,
        )

        clear_cache()

    @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver.make_salesforce_driver")
    @patch("dlt.secrets")
    def test_get_driver_with_string_credentials_uses_cache(self, mock_secrets, mock_make_driver):
        """Test that string credentials path uses cache."""
        mock_driver = Mock()
        mock_make_driver.return_value = mock_driver

        mock_creds_dict = {
            "user_name": "test@example.com",
            "password": "test_password",
            "security_token": "test_token",
        }
        mock_secrets.__getitem__.return_value = mock_creds_dict

        # First call - should create and cache
        result1 = get_salesforce_driver("salesforce.dev")

        # Second call - should return cached
        result2 = get_salesforce_driver("salesforce.dev")

        # Should return same instance
        assert result1 is result2
        assert result1 is mock_driver

        # make_salesforce_driver should only be called once (cached second time)
        assert mock_make_driver.call_count == 1

    @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver.make_salesforce_driver")
    def test_get_driver_with_credential_object_no_cache(self, mock_make_driver):
        """Test that credential object bypasses cache."""
        mock_driver1 = Mock()
        mock_driver2 = Mock()
        mock_make_driver.side_effect = [mock_driver1, mock_driver2]

        creds = SecurityTokenAuth(
            user_name="test@example.com",
            password="test_password",
            security_token="test_token",
        )

        # First call
        result1 = get_salesforce_driver(creds)

        # Second call with same credentials
        result2 = get_salesforce_driver(creds)

        # Should create new instances each time (no caching)
        assert result1 is mock_driver1
        assert result2 is mock_driver2
        assert mock_make_driver.call_count == 2

    @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver.make_salesforce_driver")
    @patch("dlt.secrets")
    def test_get_driver_different_paths_different_cache(self, mock_secrets, mock_make_driver):
        """Test that different credential paths create different cache entries."""
        mock_driver_dev = Mock()
        mock_driver_prod = Mock()
        mock_make_driver.side_effect = [mock_driver_dev, mock_driver_prod]

        mock_secrets.__getitem__.side_effect = [
            {
                "user_name": "dev@example.com",
                "password": "pass",
                "security_token": "token",
            },
            {
                "user_name": "prod@example.com",
                "password": "pass",
                "security_token": "token",
            },
        ]

        result_dev = get_salesforce_driver("salesforce.dev")
        result_prod = get_salesforce_driver("salesforce.prod")

        # Should be different instances
        assert result_dev is mock_driver_dev
        assert result_prod is mock_driver_prod
        assert result_dev is not result_prod
        assert mock_make_driver.call_count == 2

        @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver.make_salesforce_driver")
        @patch("dlt.config")
        @patch("dlt.secrets")
        def test_get_driver_with_custom_config(self, mock_secrets, mock_config, mock_make_driver):
            mock_driver = Mock()
            mock_make_driver.return_value = mock_driver

            mock_secrets.__getitem__.return_value = {
                "user_name": "test@example.com",
                "password": "password",
                "security_token": "token",
                "domain": "test",
            }
            mock_config.__getitem__.return_value = {
                "version": "v58.0",
                "domain": "test",
            }

            result = get_salesforce_driver("salesforce.dev")

            assert result is mock_driver
            call_args = mock_make_driver.call_args
            cfg = call_args[1]["config"]
            assert isinstance(cfg, SalesforceDriverConfiguration)
            assert cfg.version == "v58.0"
            assert cfg.domain == "test"

        @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver.with_config")
        @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver.make_salesforce_driver")
        @patch("dlt.secrets")
        def test_get_driver_with_custom_session(
            self, mock_secrets, mock_make_driver, mock_with_config
        ):
            """Test get_salesforce_driver with custom session."""
            mock_driver = Mock()
            mock_make_driver.return_value = mock_driver
            mock_session = Mock()

            # Make with_config a no-op - just return the original function
            mock_with_config.side_effect = lambda f: f

            # Minimal secrets to pass the sf_credential = dlt.secrets[...] line
            mock_secrets.__getitem__.return_value = {
                "user_name": "test@example.com",
                "password": "password",
                "security_token": "token",
            }

            result = get_salesforce_driver("salesforce.dev", session=mock_session)

            assert result is mock_driver

            # Verify session was passed
            call_args = mock_make_driver.call_args
            assert call_args[1]["session"] == mock_session

    def test_get_driver_invalid_credentials_type_raises_error(self):
        """Test that invalid credentials type raises ValueError."""
        with pytest.raises(ValueError, match="incorrect credentials"):
            get_salesforce_driver(12345)  # Invalid type

        with pytest.raises(ValueError, match="incorrect credentials"):
            get_salesforce_driver(["list", "of", "values"])

    @patch(
        "stairway_to_salesforce.drivers.salesforce_driver.sfdriver.with_config",
        side_effect=lambda f: f,
    )
    @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver.make_salesforce_driver")
    @patch("dlt.secrets")
    def test_get_driver_with_dict_credentials(
        self, mock_secrets, mock_make_driver, mock_with_config
    ):
        """Test string credentials path (equivalent to dict credentials)."""
        mock_driver = Mock()
        mock_make_driver.return_value = mock_driver

        mock_secrets.__getitem__.return_value = {
            "user_name": "test@example.com",
            "password": "password",
            "security_token": "token",
        }

        result = get_salesforce_driver("salesforce.dev")

        assert result is mock_driver
        mock_make_driver.assert_called_once()


class TestGetSalesforceDriverCaching:
    """Detailed tests for caching behavior."""

    def setup_method(self):
        """Clear cache before each test."""
        from stairway_to_salesforce.drivers.salesforce_driver.sfdriver_cache_manager import (
            clear_cache,
        )

        clear_cache()

    @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver.make_salesforce_driver")
    @patch("dlt.secrets")
    def test_cache_hit_returns_same_instance(self, mock_secrets, mock_make_driver):
        """Test that cache hit returns exact same driver instance."""
        mock_driver = Mock()
        mock_driver.test_attr = "test_value"
        mock_make_driver.return_value = mock_driver

        mock_secrets.__getitem__.return_value = {
            "user_name": "test@example.com",
            "password": "password",
            "security_token": "token",
        }

        result1 = get_salesforce_driver("salesforce.dev")
        result2 = get_salesforce_driver("salesforce.dev")

        # Should be same object (identity check)
        assert result1 is result2
        assert id(result1) == id(result2)
        assert result1.test_attr == "test_value"

    @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver.make_salesforce_driver")
    @patch("dlt.secrets")
    def test_cache_key_based_on_secrets_path(self, mock_secrets, mock_make_driver):
        """Test that cache key is based on secrets path, not credential values."""
        mock_driver1 = Mock()
        mock_driver2 = Mock()
        mock_make_driver.side_effect = [mock_driver1, mock_driver2]

        # Same credentials but different paths
        same_creds = {
            "user_name": "test@example.com",
            "password": "password",
            "security_token": "token",
        }
        mock_secrets.__getitem__.side_effect = [same_creds, same_creds]

        result1 = get_salesforce_driver("salesforce.path1")
        result2 = get_salesforce_driver("salesforce.path2")

        # Different cache entries despite same credentials
        assert result1 is not result2
        assert mock_make_driver.call_count == 2

    @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver.make_salesforce_driver")
    @patch("dlt.secrets")
    def test_cache_multiple_environments(self, mock_secrets, mock_make_driver):
        """Test caching across multiple environments."""
        drivers = [Mock() for _ in range(4)]
        mock_make_driver.side_effect = drivers

        mock_secrets.__getitem__.side_effect = [
            {
                "user_name": f"env{i}@example.com",
                "password": "pass",
                "security_token": "token",
            }
            for i in range(4)
        ]

        envs = [
            "salesforce.dev",
            "salesforce.staging",
            "salesforce.prod",
            "salesforce.sandbox",
        ]

        # Create drivers for each env
        results = [get_salesforce_driver(env) for env in envs]

        # All should be different
        assert len(set(id(r) for r in results)) == 4

        # Second access should use cache
        results2 = [get_salesforce_driver(env) for env in envs]

        # Should be same instances
        for r1, r2 in zip(results, results2):
            assert r1 is r2

        # make_salesforce_driver called only 4 times (once per env)
        assert mock_make_driver.call_count == 4

    @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver.make_salesforce_driver")
    def test_no_cache_for_credential_objects(self, mock_make_driver):
        """Test that credential objects always create new drivers."""
        mock_make_driver.side_effect = [Mock() for _ in range(5)]

        creds = SecurityTokenAuth(
            user_name="test@example.com", password="password", security_token="token"
        )

        results = [get_salesforce_driver(creds) for _ in range(5)]

        # All should be different instances
        assert len(set(id(r) for r in results)) == 5
        assert mock_make_driver.call_count == 5


class TestGetSalesforceDriverIntegration:
    """Integration tests with actual factory and cache."""

    def setup_method(self):
        """Clear cache before each test."""
        from stairway_to_salesforce.drivers.salesforce_driver.sfdriver_cache_manager import (
            clear_cache,
        )

        clear_cache()

    @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver_factory.Salesforce")
    @patch("dlt.secrets")
    def test_full_workflow_string_credentials(self, mock_secrets, mock_sf_class):
        """Test complete workflow with string credentials."""
        mock_sf_instance = Mock()
        mock_sf_class.return_value = mock_sf_instance

        mock_secrets.__getitem__.return_value = {
            "user_name": "test@example.com",
            "password": "test_password",
            "security_token": "test_token",
        }

        # First call - creates driver and caches
        result1 = get_salesforce_driver("salesforce.dev")

        assert result1 is mock_sf_instance
        assert mock_sf_class.call_count == 1

        # Second call - uses cache
        result2 = get_salesforce_driver("salesforce.dev")

        assert result2 is mock_sf_instance
        assert result2 is result1
        assert mock_sf_class.call_count == 1  # Not called again

    @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver_factory.Salesforce")
    def test_full_workflow_credential_object(self, mock_sf_class):
        """Test complete workflow with credential object."""
        mock_sf_instance1 = Mock()
        mock_sf_instance2 = Mock()
        mock_sf_class.side_effect = [mock_sf_instance1, mock_sf_instance2]

        creds = SecurityTokenAuth(
            user_name="test@example.com",
            password="test_password",
            security_token="test_token",
        )

        result1 = get_salesforce_driver(creds)
        result2 = get_salesforce_driver(creds)

        assert result1 is mock_sf_instance1
        assert result2 is mock_sf_instance2
        assert result1 is not result2
        assert mock_sf_class.call_count == 2


class TestGetSalesforceDriverErrorHandling:
    """Tests for error handling in get_salesforce_driver."""

    @patch("dlt.secrets")
    def test_get_driver_missing_secrets_path(self, mock_secrets):
        """Test error when secrets path doesn't exist."""
        mock_secrets.__getitem__.side_effect = KeyError("Secret not found")

        with pytest.raises(ValueError, match="Failed to load credentials"):
            get_salesforce_driver("salesforce.nonexistent")

    @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver.make_salesforce_driver")
    @patch("dlt.secrets")
    def test_get_driver_propagates_factory_errors(self, mock_secrets, mock_make_driver):
        """Test that errors from make_salesforce_driver are propagated."""
        mock_secrets.__getitem__.return_value = {
            "user_name": "test@example.com",
            "password": "password",
            "security_token": "token",
        }

        mock_make_driver.side_effect = RuntimeError("Connection failed")

        with pytest.raises(RuntimeError, match="Connection failed"):
            get_salesforce_driver("salesforce.dev")

    def test_get_driver_with_none_credentials(self):
        """Test that None credentials raises ValueError."""
        with pytest.raises(ValueError, match="incorrect credentials"):
            get_salesforce_driver(None)


class TestGetSalesforceDriverEdgeCases:
    """Tests for edge cases."""

    def setup_method(self):
        """Clear cache before each test."""
        from stairway_to_salesforce.drivers.salesforce_driver.sfdriver_cache_manager import (
            clear_cache,
        )

        clear_cache()

    @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver.make_salesforce_driver")
    @patch("dlt.secrets")
    def test_get_driver_empty_string_path(self, mock_secrets, mock_make_driver):
        """Test get_salesforce_driver with empty string path."""
        mock_driver = Mock()
        mock_make_driver.return_value = mock_driver

        mock_secrets.__getitem__.return_value = {
            "user_name": "test@example.com",
            "password": "password",
            "security_token": "token",
        }

        # Should work (creates cache key from empty string)
        result = get_salesforce_driver("")

        assert result is mock_driver

    @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver.make_salesforce_driver")
    @patch("dlt.secrets")
    def test_get_driver_unicode_path(self, mock_secrets, mock_make_driver):
        """Test get_salesforce_driver with unicode in path."""
        mock_driver = Mock()
        mock_make_driver.return_value = mock_driver

        mock_secrets.__getitem__.return_value = {
            "user_name": "test@example.com",
            "password": "password",
            "security_token": "token",
        }

        result = get_salesforce_driver("salesforce.日本語")

        assert result is mock_driver

    @patch("stairway_to_salesforce.drivers.salesforce_driver.sfdriver.make_salesforce_driver")
    def test_get_driver_with_all_credential_types(self, mock_make_driver):
        """Test get_salesforce_driver works with all credential types."""
        mock_make_driver.return_value = Mock()

        credential_types = [
            SecurityTokenAuth(
                user_name="test@example.com", password="pass", security_token="token"
            ),
            ConsumerKeySecretDomainAuth(
                consumer_key="key", consumer_secret="secret", domain="test"
            ),
        ]

        for creds in credential_types:
            result = get_salesforce_driver(creds)
            assert result is not None
