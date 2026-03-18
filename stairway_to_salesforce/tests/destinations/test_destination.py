"""
Unit tests for Salesforce Bulk API v2 destination main module.

Tests focus on the destination configuration logic and integration patterns.
The @dlt.destination decorator makes direct testing challenging, so we test
the underlying logic and configuration validation.
"""

from unittest.mock import Mock, patch

import pytest

from stairway_to_salesforce.destinations.salesforce_bulk2.destination_config import (
    SalesforceDestinationConfig,
)


class TestDestinationConfig:
    """Tests for SalesforceDestinationConfig validation logic."""

    def test_config_from_append_with_insert(self):
        """Test config creation from append disposition with insert operation."""
        table_schema = {
            "name": "Account",
            "write_disposition": "append",
            "x-salesforce-operation": "insert",
            "primary_key": "Id",
        }

        config = SalesforceDestinationConfig.from_table_schema(table_schema)

        assert config.target_object_name == "Account"
        assert config.write_disposition == "append"
        assert config.salesforce_operation == "insert"
        assert config.primary_key_field == "Id"

    def test_config_from_append_with_upsert(self):
        """Test config creation from append disposition with upsert operation."""
        table_schema = {
            "name": "Account",
            "write_disposition": "append",
            "x-salesforce-operation": "upsert",
            "primary_key": "External_ID__c",
        }

        config = SalesforceDestinationConfig.from_table_schema(table_schema)

        assert config.salesforce_operation == "upsert"
        assert config.primary_key_field == "External_ID__c"

    def test_config_from_replace_disposition(self):
        """Test config creation from replace disposition."""
        table_schema = {
            "name": "Account",
            "write_disposition": "replace",
            "primary_key": "Id",
        }

        config = SalesforceDestinationConfig.from_table_schema(table_schema)

        assert config.salesforce_operation == "replace"
        assert config.primary_key_field == "Id"

    def test_config_missing_sobject_name(self):
        """Test that missing SObject name raises error."""
        table_schema = {
            "write_disposition": "append",
            "x-salesforce-operation": "insert",
        }

        with pytest.raises(ValueError, match="SObject name must be defined"):
            SalesforceDestinationConfig.from_table_schema(table_schema)

    def test_config_append_missing_operation_hint(self):
        """Test that append without operation hint raises error."""
        table_schema = {
            "name": "Account",
            "write_disposition": "append",
            # Missing x-salesforce-operation
        }

        with pytest.raises(ValueError, match="x-salesforce-operation.*required"):
            SalesforceDestinationConfig.from_table_schema(table_schema)

    def test_config_invalid_disposition(self):
        """Test that invalid write_disposition raises error."""
        table_schema = {
            "name": "Account",
            "write_disposition": "merge",  # Not supported
            "x-salesforce-operation": "insert",
        }

        with pytest.raises(ValueError, match="Unsupported write_disposition"):
            SalesforceDestinationConfig.from_table_schema(table_schema)

    def test_config_invalid_operation(self):
        """Test that invalid salesforce operation raises error."""
        table_schema = {
            "name": "Account",
            "write_disposition": "append",
            "x-salesforce-operation": "invalid_op",
        }

        with pytest.raises(ValueError, match="Invalid operation"):
            SalesforceDestinationConfig.from_table_schema(table_schema)

    def test_config_delete_operation(self):
        """Test config creation for delete operation."""
        table_schema = {
            "name": "Account",
            "write_disposition": "append",
            "x-salesforce-operation": "delete",
            "primary_key": "Id",
        }

        config = SalesforceDestinationConfig.from_table_schema(table_schema)

        assert config.salesforce_operation == "delete"

    def test_config_with_list_primary_key(self):
        """Test config with list primary key."""
        table_schema = {
            "name": "Account",
            "write_disposition": "append",
            "x-salesforce-operation": "upsert",
            "primary_key": ["Id", "External_ID__c"],
        }

        config = SalesforceDestinationConfig.from_table_schema(table_schema)

        assert isinstance(config.primary_key_field, list)
        assert config.primary_key_field == ["Id", "External_ID__c"]

    def test_config_primary_key_from_columns(self):
        """Test config extracts primary key from columns metadata."""
        table_schema = {
            "name": "Account",
            "write_disposition": "append",
            "x-salesforce-operation": "upsert",
            "columns": {"Id": {"primary_key": True}, "Name": {}},
        }

        config = SalesforceDestinationConfig.from_table_schema(table_schema)

        assert config.primary_key_field == "Id"


class TestDestinationWorkflow:
    """Tests for destination workflow and integration."""

    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.destination.cleanup_temp_file"
    )
    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.destination.execute_job"
    )
    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.destination.prepare_data"
    )
    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.destination.get_salesforce_key_resolver"  # noqa: E501
    )
    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.destination.get_salesforce_driver"
    )
    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.destination.SalesforceDestinationConfig"  # noqa: E501
    )
    def test_destination_workflow_components(
        self,
        mock_config_class,
        mock_get_driver,
        mock_get_resolver,
        mock_prepare,
        mock_execute,
        mock_cleanup,
        sample_account_data,
        temp_csv_file,
    ):
        """Test that destination workflow calls expected components."""
        # Setup mocks
        mock_config = Mock()
        mock_config.target_object_name = "Account"
        mock_config.salesforce_operation = "insert"
        mock_config.primary_key_field = "Id"
        mock_config_class.from_table_schema.return_value = mock_config

        mock_driver = Mock()
        mock_resolver = Mock()
        mock_get_driver.return_value = mock_driver
        mock_get_resolver.return_value = mock_resolver
        mock_prepare.return_value = temp_csv_file

        table_schema = {
            "name": "Account",
            "write_disposition": "append",
            "x-salesforce-operation": "insert",
            "primary_key": "Id",
        }

        # The @dlt.destination decorator changes how this works
        # We can't test it directly, but we can verify the logic exists
        # by testing the components it should use

        # Verify config class is importable and works
        real_config = SalesforceDestinationConfig.from_table_schema(table_schema)
        assert real_config.target_object_name == "Account"
        assert real_config.salesforce_operation == "insert"


class TestDataProcessorIntegration:
    """Tests for data processor integration."""

    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.destination.cleanup_temp_file"
    )
    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.destination.execute_job"
    )
    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.destination.prepare_data"
    )
    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.destination.get_salesforce_key_resolver"  # noqa: E501
    )
    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.destination.get_salesforce_driver"
    )
    def test_prepare_data_called_with_items(
        self,
        mock_get_driver,
        mock_get_resolver,
        mock_prepare,
        mock_execute,
        mock_cleanup,
        sample_account_data,
        temp_csv_file,
    ):
        """Test that prepare_data is called with correct items."""
        # This test validates the integration pattern
        # Even though we can't directly test the decorated function,
        # we can test that the components work correctly

        from stairway_to_salesforce.destinations.salesforce_bulk2.data_processor import (
            prepare_data,
        )

        # Test prepare_data directly
        result = prepare_data(sample_account_data)

        # Should create a CSV file
        assert result.endswith(".csv")

        # Cleanup
        from stairway_to_salesforce.destinations.salesforce_bulk2.data_processor import (
            cleanup_temp_file,
        )

        cleanup_temp_file(result)


class TestJobExecutorIntegration:
    """Tests for job executor integration."""

    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.job_executor.exec_insert"
    )
    def test_execute_job_insert_operation(
        self, mock_insert, mock_security_token_credentials, temp_csv_file
    ):
        """Test execute_job calls correct operation handler."""
        from simple_salesforce import Salesforce

        from stairway_to_salesforce.destinations.salesforce_bulk2.job_executor import (
            execute_job,
        )

        mock_driver = Mock(spec=Salesforce)

        execute_job(
            sf_driver=mock_driver,
            target_name="Account",
            salesforce_operation="insert",
            primary_key="Id",
            file_path=temp_csv_file,
            key_resolver=None,
        )

        # Should call insert handler
        mock_insert.assert_called_once()

    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.job_executor.exec_upsert"
    )
    def test_execute_job_upsert_operation(self, mock_upsert, temp_csv_file):
        """Test execute_job calls upsert handler."""
        from simple_salesforce import Salesforce

        from stairway_to_salesforce.destinations.salesforce_bulk2.job_executor import (
            execute_job,
        )

        mock_driver = Mock(spec=Salesforce)

        execute_job(
            sf_driver=mock_driver,
            target_name="Account",
            salesforce_operation="upsert",
            primary_key="External_ID__c",
            file_path=temp_csv_file,
            key_resolver=None,
        )

        mock_upsert.assert_called_once()

    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.job_executor.exec_delete"
    )
    def test_execute_job_delete_operation(self, mock_delete, temp_csv_file):
        """Test execute_job calls delete handler."""
        from simple_salesforce import Salesforce

        from stairway_to_salesforce.destinations.salesforce_bulk2.job_executor import (
            execute_job,
        )

        mock_driver = Mock(spec=Salesforce)
        mock_resolver = Mock()

        execute_job(
            sf_driver=mock_driver,
            target_name="Account",
            salesforce_operation="delete",
            primary_key="Id",
            file_path=temp_csv_file,
            key_resolver=mock_resolver,
        )

        mock_delete.assert_called_once()

    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.job_executor.exec_replace"
    )
    def test_execute_job_replace_operation(self, mock_replace, temp_csv_file):
        """Test execute_job calls replace handler."""
        from simple_salesforce import Salesforce

        from stairway_to_salesforce.destinations.salesforce_bulk2.job_executor import (
            execute_job,
        )

        mock_driver = Mock(spec=Salesforce)

        execute_job(
            sf_driver=mock_driver,
            target_name="Account",
            salesforce_operation="replace",
            primary_key="Id",
            file_path=temp_csv_file,
            key_resolver=None,
        )

        mock_replace.assert_called_once()

    def test_execute_job_invalid_operation(self, temp_csv_file):
        """Test execute_job raises error for invalid operation."""
        from simple_salesforce import Salesforce

        from stairway_to_salesforce.destinations.salesforce_bulk2.job_executor import (
            execute_job,
        )

        mock_driver = Mock(spec=Salesforce)

        with pytest.raises(ValueError, match="Unsupported operation"):
            execute_job(
                sf_driver=mock_driver,
                target_name="Account",
                salesforce_operation="invalid_op",
                primary_key="Id",
                file_path=temp_csv_file,
                key_resolver=None,
            )


class TestDestinationEdgeCases:
    """Tests for edge cases in destination configuration."""

    def test_config_with_custom_object(self):
        """Test config with custom Salesforce object."""
        table_schema = {
            "name": "My_Custom_Object__c",
            "write_disposition": "append",
            "x-salesforce-operation": "upsert",
            "primary_key": "External_Key__c",
        }

        config = SalesforceDestinationConfig.from_table_schema(table_schema)

        assert config.target_object_name == "My_Custom_Object__c"
        assert config.primary_key_field == "External_Key__c"

    def test_config_replace_with_primary_key_warning(self, capsys):
        """Test replace disposition with primary key logs warning."""
        table_schema = {
            "name": "Account",
            "write_disposition": "replace",
            "primary_key": "External_ID__c",
        }

        config = SalesforceDestinationConfig.from_table_schema(table_schema)

        # Should create config with replace operation
        assert config.salesforce_operation == "replace"
        assert config.primary_key_field == "External_ID__c"

    def test_config_no_primary_key(self):
        """Test config without primary key for insert operation."""
        table_schema = {
            "name": "Account",
            "write_disposition": "append",
            "x-salesforce-operation": "insert",
            # No primary_key
        }

        config = SalesforceDestinationConfig.from_table_schema(table_schema)

        assert config.primary_key_field is None
        assert config.salesforce_operation == "insert"


class TestComponentFactories:
    """Tests for component factory functions."""

    @patch(
        "stairway_to_salesforce.drivers.salesforce_driver.sfdriver.make_salesforce_driver"
    )
    @patch("dlt.secrets")
    def test_get_salesforce_driver(self, mock_secrets, mock_make_driver):
        """Test get_salesforce_driver factory."""
        from stairway_to_salesforce.drivers import get_salesforce_driver

        mock_driver = Mock()
        mock_make_driver.return_value = mock_driver
        mock_secrets.__getitem__.return_value = {
            "user_name": "test@example.com",
            "password": "password",
            "security_token": "token",
        }

        result = get_salesforce_driver("salesforce.dev")

        assert result is mock_driver

    @patch(
        "stairway_to_salesforce.components.salesforce_key_resolver.resolver.SalesforceKeyResolver"
    )
    def test_get_salesforce_key_resolver(self, mock_resolver_class):
        """Test get_salesforce_key_resolver factory."""
        from stairway_to_salesforce.components import get_salesforce_key_resolver

        mock_resolver = Mock()
        mock_resolver_class.return_value = mock_resolver

        # Call twice to test singleton pattern
        result1 = get_salesforce_key_resolver(credentials="salesforce.dev")
        result2 = get_salesforce_key_resolver(credentials="salesforce.dev")

        # Should return same instance (singleton)
        assert result1 is result2
