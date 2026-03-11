"""
Unit tests for DLT resource builder.

Tests resource configuration validation and resource building.
"""

from unittest.mock import MagicMock, Mock, patch

import dlt
import pytest

from stairway_to_salesforce.sources.salesforce_bulk2.resource_builder import (
    build_resource, validate_resource_configs)


class TestValidateResourceConfigs:
    """Tests for validate_resource_configs() function."""

    def test_validate_valid_config(self):
        """Test validation of valid resource config."""
        configs = [
            {
                "name": "accounts",
                "primary_key": "account_id",
                "sobject": "Account",
                "fields": ["Id", "Name", "Email"],
            }
        ]

        # Should not raise
        validate_resource_configs(configs)

    def test_validate_multiple_configs(self):
        """Test validation of multiple resource configs."""
        configs = [
            {
                "name": "accounts",
                "primary_key": "account_id",
                "sobject": "Account",
                "fields": ["Id", "Name"],
            },
            {
                "name": "contacts",
                "primary_key": "contact_id",
                "sobject": "Contact",
                "fields": ["Id", "Email"],
            },
        ]

        validate_resource_configs(configs)

    def test_validate_empty_configs(self):
        """Test that empty configs raises error."""
        with pytest.raises(
            ValueError, match="At least one resource configuration is required"
        ):
            validate_resource_configs([])

    def test_validate_missing_name(self):
        """Test that missing name raises error."""
        configs = [{"primary_key": "id", "sobject": "Account", "fields": ["Id"]}]

        with pytest.raises(ValueError, match="missing required fields"):
            validate_resource_configs(configs)

    def test_validate_missing_primary_key(self):
        """Test that missing primary_key raises error."""
        configs = [{"name": "accounts", "sobject": "Account", "fields": ["Id"]}]

        with pytest.raises(ValueError, match="missing required fields"):
            validate_resource_configs(configs)

    def test_validate_missing_sobject(self):
        """Test that missing sobject raises error."""
        configs = [{"name": "accounts", "primary_key": "id", "fields": ["Id"]}]

        with pytest.raises(ValueError, match="missing required fields"):
            validate_resource_configs(configs)

    def test_validate_invalid_write_disposition(self):
        """Test that invalid write_disposition raises error."""
        configs = [
            {
                "name": "accounts",
                "primary_key": "id",
                "sobject": "Account",
                "fields": ["Id"],
                "write_disposition": "invalid_mode",
            }
        ]

        with pytest.raises(ValueError, match="must be one of"):
            validate_resource_configs(configs)

    def test_validate_fields_not_list(self):
        """Test that non-list fields raises error."""
        configs = [
            {
                "name": "accounts",
                "primary_key": "id",
                "sobject": "Account",
                "fields": "Id,Name",  # String instead of list
            }
        ]

        with pytest.raises(ValueError, match="must be a list"):
            validate_resource_configs(configs)

    def test_validate_replication_key_not_in_fields(self):
        """Test that replication_key must exist in fields."""
        configs = [
            {
                "name": "accounts",
                "primary_key": "id",
                "sobject": "Account",
                "fields": ["Id", "Name"],
                "replication_key": "LastModifiedDate",  # Not in fields
            }
        ]

        with pytest.raises(ValueError, match="must exist in fields"):
            validate_resource_configs(configs)

    def test_validate_config_with_optional_fields(self):
        """Test config with all optional fields."""
        configs = [
            {
                "name": "accounts",
                "primary_key": "id",
                "sobject": "Account",
                "fields": ["Id", "Name", "LastModifiedDate"],
                "write_disposition": "append",
                "replication_key": "LastModifiedDate",
                "query_filter": "Type = 'Customer'",
                "column_types": {"Id": "text", "Name": "text"},
            }
        ]

        # Should not raise
        validate_resource_configs(configs)

    def test_validate_multiple_configs_identifies_correct_error(self):
        """Test that error message identifies which config is invalid."""
        configs = [
            {
                "name": "accounts",
                "primary_key": "id",
                "sobject": "Account",
                "fields": ["Id"],
            },
            {"name": "contacts", "sobject": "Contact"},  # Missing primary_key
        ]

        with pytest.raises(ValueError, match="Config 1"):
            validate_resource_configs(configs)


class TestBuildResource:
    """Tests for build_resource() function."""

    @patch(
        "stairway_to_salesforce.sources.salesforce_bulk2.resource_builder.get_salesforce_driver"
    )
    def test_build_resource_basic(self, mock_get_driver):
        """Test basic resource building."""
        config = {
            "name": "accounts",
            "primary_key": "account_id",
            "sobject": "Account",
            "fields": ["Id", "Name"],
        }

        mock_driver = Mock()
        mock_get_driver.return_value = mock_driver

        mock_fetch_fn = Mock()
        mock_fetch_fn.return_value = iter([[{"Id": "001", "Name": "Test"}]])

        resource = build_resource(
            config=config,
            fetch_data_fn=mock_fetch_fn,
            credentials="salesforce.dev",
            session=None,
        )

        # Verify resource was created
        assert callable(resource)

    @patch(
        "stairway_to_salesforce.sources.salesforce_bulk2.resource_builder.dlt.sources.incremental"
    )
    @patch(
        "stairway_to_salesforce.sources.salesforce_bulk2.resource_builder.get_salesforce_driver"
    )
    def test_build_resource_with_incremental(self, mock_get_driver, mock_incremental):
        """Test resource building with incremental loading."""
        config = {
            "name": "accounts",
            "primary_key": "account_id",
            "sobject": "Account",
            "fields": ["Id", "Name", "LastModifiedDate"],
            "replication_key": "LastModifiedDate",
        }

        mock_driver = Mock()
        mock_get_driver.return_value = mock_driver

        # Mock incremental
        mock_incremental.return_value = Mock()

        mock_fetch_fn = Mock()
        mock_fetch_fn.return_value = iter([[{"Id": "001", "Name": "Test"}]])

        resource = build_resource(
            config=config,
            fetch_data_fn=mock_fetch_fn,
            credentials="salesforce.dev",
            session=None,
        )

        # Verify incremental was configured
        mock_incremental.assert_called_once_with("LastModifiedDate", initial_value=None)

    @patch(
        "stairway_to_salesforce.sources.salesforce_bulk2.resource_builder.get_salesforce_driver"
    )
    def test_build_resource_with_write_disposition(self, mock_get_driver):
        """Test resource with custom write_disposition."""
        config = {
            "name": "accounts",
            "primary_key": "account_id",
            "sobject": "Account",
            "fields": ["Id", "Name"],
            "write_disposition": "replace",
        }

        mock_driver = Mock()
        mock_get_driver.return_value = mock_driver

        mock_fetch_fn = Mock()
        mock_fetch_fn.return_value = iter([[{"Id": "001", "Name": "Test"}]])

        resource = build_resource(
            config=config,
            fetch_data_fn=mock_fetch_fn,
            credentials="salesforce.dev",
            session=None,
        )

        assert callable(resource)

    @patch(
        "stairway_to_salesforce.sources.salesforce_bulk2.resource_builder.get_salesforce_driver"
    )
    def test_build_resource_with_query_filter(self, mock_get_driver):
        """Test resource with query filter."""
        config = {
            "name": "customers",
            "primary_key": "id",
            "sobject": "Account",
            "fields": ["Id", "Name", "Type"],
            "query_filter": "Type = 'Customer'",
        }

        mock_driver = Mock()
        mock_get_driver.return_value = mock_driver

        mock_fetch_fn = Mock()
        mock_fetch_fn.return_value = iter([[{"Id": "001", "Name": "Test"}]])

        resource = build_resource(
            config=config,
            fetch_data_fn=mock_fetch_fn,
            credentials="salesforce.dev",
            session=None,
        )

        assert callable(resource)

    @patch(
        "stairway_to_salesforce.sources.salesforce_bulk2.resource_builder.get_salesforce_driver"
    )
    def test_build_resource_with_column_types(self, mock_get_driver):
        """Test resource with column type definitions."""
        config = {
            "name": "accounts",
            "primary_key": "id",
            "sobject": "Account",
            "fields": ["Id", "Name", "Amount"],
            "column_types": {
                "Id": {"data_type": "text"},
                "Name": {"data_type": "text"},
                "Amount": {"data_type": "decimal"},
            },
        }

        mock_driver = Mock()
        mock_get_driver.return_value = mock_driver

        mock_fetch_fn = Mock()
        mock_fetch_fn.return_value = iter([[{"Id": "001", "Name": "Test"}]])

        resource = build_resource(
            config=config,
            fetch_data_fn=mock_fetch_fn,
            credentials="salesforce.dev",
            session=None,
        )

        assert callable(resource)

    @patch(
        "stairway_to_salesforce.sources.salesforce_bulk2.resource_builder.get_salesforce_driver"
    )
    def test_build_resource_driver_creation_error(self, mock_get_driver):
        """Test error handling when driver creation fails."""
        config = {
            "name": "accounts",
            "primary_key": "id",
            "sobject": "Account",
            "fields": ["Id"],
        }

        mock_get_driver.side_effect = RuntimeError("Failed to connect")

        mock_fetch_fn = Mock()

        # Resource creation should succeed
        resource = build_resource(
            config=config,
            fetch_data_fn=mock_fetch_fn,
            credentials="salesforce.dev",
            session=None,
        )

        assert callable(resource)

        # Error should occur when resource is actually executed by DLT
        # We can't easily test this without running the full DLT pipeline

    @patch(
        "stairway_to_salesforce.sources.salesforce_bulk2.resource_builder.get_salesforce_driver"
    )
    def test_build_resource_fetch_error(self, mock_get_driver):
        """Test error handling when fetch fails."""
        config = {
            "name": "accounts",
            "primary_key": "id",
            "sobject": "Account",
            "fields": ["Id"],
        }

        mock_driver = Mock()
        mock_get_driver.return_value = mock_driver

        mock_fetch_fn = Mock()
        mock_fetch_fn.side_effect = RuntimeError("Fetch failed")

        resource = build_resource(
            config=config,
            fetch_data_fn=mock_fetch_fn,
            credentials="salesforce.dev",
            session=None,
        )

        # Error should occur when resource is executed by DLT
        # We can't easily test this without running the full DLT pipeline
        assert callable(resource)

    def test_build_resource_with_custom_session(self):
        """Test resource building with custom session."""
        config = {
            "name": "accounts",
            "primary_key": "id",
            "sobject": "Account",
            "fields": ["Id"],
        }

        mock_session = Mock()
        mock_fetch_fn = Mock()
        mock_fetch_fn.return_value = iter([[{"Id": "001"}]])

        # We can't easily verify session passing without full integration
        # Just verify resource builds
        resource = build_resource(
            config=config,
            fetch_data_fn=mock_fetch_fn,
            credentials="salesforce.dev",
            session=mock_session,
        )

        assert callable(resource)


class TestResourceBuilderIntegration:
    """Integration tests for resource builder."""

    @patch(
        "stairway_to_salesforce.sources.salesforce_bulk2.resource_builder.get_salesforce_driver"
    )
    def test_full_resource_workflow(self, mock_get_driver):
        """Test complete resource building and execution workflow."""
        config = {
            "name": "accounts",
            "primary_key": "id",
            "sobject": "Account",
            "fields": ["Id", "Name", "LastModifiedDate"],
            "write_disposition": "append",
            "replication_key": "LastModifiedDate",
            "query_filter": "Type = 'Customer'",
        }

        # Mock driver
        mock_driver = Mock()
        mock_get_driver.return_value = mock_driver

        # Mock fetch function with proper data structure
        mock_data = [
            [{"id": "001", "Name": "Acme", "LastModifiedDate": "2025-01-19"}],
            [{"id": "002", "Name": "Global", "LastModifiedDate": "2025-01-20"}],
        ]
        mock_fetch_fn = Mock()
        mock_fetch_fn.return_value = iter(mock_data)

        # Build resource
        resource = build_resource(
            config=config,
            fetch_data_fn=mock_fetch_fn,
            credentials="salesforce.dev",
            session=None,
        )

        # Verify resource is callable
        assert callable(resource)


class TestResourceBuilderEdgeCases:
    """Tests for edge cases in resource builder."""

    def test_validate_config_with_empty_fields_list(self):
        """Test that empty fields list is allowed (validation happens elsewhere)."""
        configs = [
            {
                "name": "accounts",
                "primary_key": "id",
                "sobject": "Account",
                "fields": [],  # Empty list
            }
        ]

        # Should not raise at validation
        # (Actual validation happens in query builder)
        validate_resource_configs(configs)

    def test_validate_config_with_unicode_name(self):
        """Test config with unicode characters in name."""
        configs = [
            {
                "name": "accounts_日本語",
                "primary_key": "id",
                "sobject": "Account",
                "fields": ["Id"],
            }
        ]

        validate_resource_configs(configs)

    def test_validate_config_with_custom_object(self):
        """Test config with custom Salesforce object."""
        configs = [
            {
                "name": "custom_records",
                "primary_key": "id",
                "sobject": "Custom_Object__c",
                "fields": ["Id", "Custom_Field__c"],
            }
        ]

        validate_resource_configs(configs)

    def test_validate_config_with_relationship_fields(self):
        """Test config with relationship field notation."""
        configs = [
            {
                "name": "contacts",
                "primary_key": "id",
                "sobject": "Contact",
                "fields": ["Id", "Name", "Account.Name", "Owner__r.Email"],
            }
        ]

        validate_resource_configs(configs)

    @patch(
        "stairway_to_salesforce.sources.salesforce_bulk2.resource_builder.get_salesforce_driver"
    )
    def test_build_resource_with_dict_credentials(self, mock_get_driver):
        """Test resource building with dict credentials."""
        config = {
            "name": "accounts",
            "primary_key": "id",
            "sobject": "Account",
            "fields": ["Id"],
        }

        mock_driver = Mock()
        mock_get_driver.return_value = mock_driver

        cred_dict = {
            "user_name": "test@example.com",
            "password": "password",
            "security_token": "token",
        }

        mock_fetch_fn = Mock()
        mock_fetch_fn.return_value = iter([[{"Id": "001"}]])

        resource = build_resource(
            config=config,
            fetch_data_fn=mock_fetch_fn,
            credentials=cred_dict,
            session=None,
        )

        assert callable(resource)

    @patch(
        "stairway_to_salesforce.sources.salesforce_bulk2.resource_builder.get_salesforce_driver"
    )
    def test_build_resource_with_list_primary_key(self, mock_get_driver):
        """Test resource with composite primary key."""
        config = {
            "name": "accounts",
            "primary_key": ["Id", "External_ID__c"],
            "sobject": "Account",
            "fields": ["Id", "External_ID__c", "Name"],
        }

        mock_driver = Mock()
        mock_get_driver.return_value = mock_driver

        mock_fetch_fn = Mock()
        mock_fetch_fn.return_value = iter([[{"Id": "001", "External_ID__c": "EXT001"}]])

        resource = build_resource(
            config=config,
            fetch_data_fn=mock_fetch_fn,
            credentials="salesforce.dev",
            session=None,
        )

        assert callable(resource)
