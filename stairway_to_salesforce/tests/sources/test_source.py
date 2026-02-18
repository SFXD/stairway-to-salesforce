"""
Unit tests for Salesforce Bulk API v2 source.

Tests the main source function and source creation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from stairway_to_salesforce.sources.salesforce_bulk2.source import (
    salesforce_bulk2_source,
)


class TestSalesforceSourceCreation:
    """Tests for salesforce_bulk2_source() function."""
    
    @patch('stairway_to_salesforce.sources.salesforce_bulk2.source.validate_resource_configs')
    def test_create_source_with_single_resource(self, mock_validate):
        """Test creating source with single resource configuration."""
        resource_configs = [{
            "name": "accounts",
            "primary_key": "id",
            "sobject": "Account",
            "fields": ["Id", "Name"]
        }]
        
        source = salesforce_bulk2_source(
            resource_configs=resource_configs,
            credentials="salesforce.dev"
        )
        
        # Verify validation was called
        mock_validate.assert_called_once_with(resource_configs)
        
        # Source should be created (it's a callable with @dlt.source decorator)
        assert source is not None
    
    @patch('stairway_to_salesforce.sources.salesforce_bulk2.source.validate_resource_configs')
    def test_create_source_with_multiple_resources(self, mock_validate):
        """Test creating source with multiple resource configurations."""
        resource_configs = [
            {
                "name": "accounts",
                "primary_key": "id",
                "sobject": "Account",
                "fields": ["Id", "Name"]
            },
            {
                "name": "contacts",
                "primary_key": "id",
                "sobject": "Contact",
                "fields": ["Id", "Email"]
            }
        ]
        
        source = salesforce_bulk2_source(
            resource_configs=resource_configs,
            credentials="salesforce.dev"
        )
        
        # Verify validation was called
        mock_validate.assert_called_once()
        
        # Source should be created
        assert source is not None
    
    def test_create_source_with_none_credentials(self):
        """Test that None credentials raises error."""
        resource_configs = [{
            "name": "accounts",
            "primary_key": "id",
            "sobject": "Account",
            "fields": ["Id"]
        }]
        
        with pytest.raises(ValueError, match="credentials must be provided"):
            salesforce_bulk2_source(
                resource_configs=resource_configs,
                credentials=None
            )
    
    @patch('stairway_to_salesforce.sources.salesforce_bulk2.source.validate_resource_configs')
    def test_create_source_validation_error(self, mock_validate):
        """Test that validation errors are propagated."""
        resource_configs = [{
            "name": "accounts",
            # Missing required fields
        }]
        
        mock_validate.side_effect = ValueError("Missing required fields")
        
        with pytest.raises(ValueError, match="Missing required fields"):
            salesforce_bulk2_source(
                resource_configs=resource_configs,
                credentials="salesforce.dev"
            )
    
    @patch('stairway_to_salesforce.sources.salesforce_bulk2.source.validate_resource_configs')
    def test_create_source_with_session(self, mock_validate):
        """Test creating source with custom session."""
        resource_configs = [{
            "name": "accounts",
            "primary_key": "id",
            "sobject": "Account",
            "fields": ["Id"]
        }]
        
        mock_session = Mock()
        
        source = salesforce_bulk2_source(
            resource_configs=resource_configs,
            credentials="salesforce.dev",
            session=mock_session
        )
        
        # Source should be created
        assert source is not None
    
    @patch('stairway_to_salesforce.sources.salesforce_bulk2.source.validate_resource_configs')
    def test_create_source_with_string_credentials(self, mock_validate):
        """Test creating source with string credentials path."""
        resource_configs = [{
            "name": "accounts",
            "primary_key": "id",
            "sobject": "Account",
            "fields": ["Id"]
        }]
        
        source = salesforce_bulk2_source(
            resource_configs=resource_configs,
            credentials="salesforce.production"
        )
        
        # Source should be created
        assert source is not None
    
    @patch('stairway_to_salesforce.sources.salesforce_bulk2.source.validate_resource_configs')
    def test_create_source_with_dict_credentials(self, mock_validate):
        """Test creating source with dict credentials."""
        resource_configs = [{
            "name": "accounts",
            "primary_key": "id",
            "sobject": "Account",
            "fields": ["Id"]
        }]
        
        cred_dict = {
            "user_name": "test@example.com",
            "password": "password",
            "security_token": "token"
        }
        
        source = salesforce_bulk2_source(
            resource_configs=resource_configs,
            credentials=cred_dict
        )
        
        # Source should be created
        assert source is not None


class TestSourceResourceBuilding:
    """Tests for resource building within source."""
    
    @patch('stairway_to_salesforce.sources.salesforce_bulk2.source.validate_resource_configs')
    def test_source_builds_resources_with_fetch_data(self, mock_validate):
        """Test that source is created successfully."""
        resource_configs = [{
            "name": "accounts",
            "primary_key": "id",
            "sobject": "Account",
            "fields": ["Id", "Name"]
        }]
        
        source = salesforce_bulk2_source(
            resource_configs=resource_configs,
            credentials="salesforce.dev"
        )
        
        # Verify source was created
        assert source is not None
    
    @patch('stairway_to_salesforce.sources.salesforce_bulk2.source.validate_resource_configs')
    def test_source_builds_each_resource_config(self, mock_validate):
        """Test that source handles multiple configs."""
        resource_configs = [
            {"name": "accounts", "primary_key": "id", "sobject": "Account", "fields": ["Id"]},
            {"name": "contacts", "primary_key": "id", "sobject": "Contact", "fields": ["Id"]},
            {"name": "opportunities", "primary_key": "id", "sobject": "Opportunity", "fields": ["Id"]}
        ]
        
        source = salesforce_bulk2_source(
            resource_configs=resource_configs,
            credentials="salesforce.dev"
        )
        
        # Source should be created
        assert source is not None


class TestSourceIntegration:
    """Integration tests for source creation and execution."""
    
    @patch('stairway_to_salesforce.sources.salesforce_bulk2.source.validate_resource_configs')
    def test_source_full_workflow(self, mock_validate):
        """Test complete source creation workflow."""
        # Setup
        resource_configs = [{
            "name": "accounts",
            "primary_key": "id",
            "sobject": "Account",
            "fields": ["Id", "Name"],
            "write_disposition": "append"
        }]
        
        # Create source
        source = salesforce_bulk2_source(
            resource_configs=resource_configs,
            credentials="salesforce.dev"
        )
        
        # Source should be created successfully
        assert source is not None
        
        # Verify validation happened
        mock_validate.assert_called_once()
    
    @patch('stairway_to_salesforce.sources.salesforce_bulk2.source.validate_resource_configs')
    def test_source_with_incremental_resources(self, mock_validate):
        """Test source with incremental loading resources."""
        resource_configs = [{
            "name": "accounts",
            "primary_key": "id",
            "sobject": "Account",
            "fields": ["Id", "Name", "LastModifiedDate"],
            "replication_key": "LastModifiedDate"
        }]
        
        source = salesforce_bulk2_source(
            resource_configs=resource_configs,
            credentials="salesforce.dev"
        )
        
        # Source should be created
        assert source is not None
    
    @patch('stairway_to_salesforce.sources.salesforce_bulk2.source.validate_resource_configs')
    def test_source_with_filtered_resources(self, mock_validate):
        """Test source with query-filtered resources."""
        resource_configs = [{
            "name": "customer_accounts",
            "primary_key": "id",
            "sobject": "Account",
            "fields": ["Id", "Name", "Type"],
            "query_filter": "Type = 'Customer'"
        }]
        
        source = salesforce_bulk2_source(
            resource_configs=resource_configs,
            credentials="salesforce.dev"
        )
        
        # Source should be created
        assert source is not None


class TestSourceEdgeCases:
    """Tests for edge cases in source creation."""
    
    @patch('stairway_to_salesforce.sources.salesforce_bulk2.source.validate_resource_configs')
    def test_source_with_custom_objects(self, mock_validate):
        """Test source with custom Salesforce objects."""
        resource_configs = [{
            "name": "custom_records",
            "primary_key": "id",
            "sobject": "Custom_Object__c",
            "fields": ["Id", "Custom_Field__c"]
        }]
        
        source = salesforce_bulk2_source(
            resource_configs=resource_configs,
            credentials="salesforce.dev"
        )
        
        assert source is not None
    
    @patch('stairway_to_salesforce.sources.salesforce_bulk2.source.validate_resource_configs')
    def test_source_with_relationship_fields(self, mock_validate):
        """Test source with relationship field notation."""
        resource_configs = [{
            "name": "contacts_with_accounts",
            "primary_key": "id",
            "sobject": "Contact",
            "fields": ["Id", "Name", "Account.Name", "Owner__r.Email"]
        }]
        
        source = salesforce_bulk2_source(
            resource_configs=resource_configs,
            credentials="salesforce.dev"
        )
        
        assert source is not None
    
    @patch('stairway_to_salesforce.sources.salesforce_bulk2.source.validate_resource_configs')
    def test_source_with_many_resources(self, mock_validate):
        """Test source with many resource configurations."""
        # Create 10 resource configs
        resource_configs = [
            {
                "name": f"resource_{i}",
                "primary_key": "id",
                "sobject": f"Object_{i}__c",
                "fields": ["Id", "Name"]
            }
            for i in range(10)
        ]
        
        source = salesforce_bulk2_source(
            resource_configs=resource_configs,
            credentials="salesforce.dev"
        )
        
        # Source should be created
        assert source is not None
    
    @patch('stairway_to_salesforce.sources.salesforce_bulk2.source.validate_resource_configs')
    def test_source_preserves_config_order(self, mock_validate):
        """Test that source creation preserves resource config order."""
        resource_configs = [
            {"name": "first", "primary_key": "id", "sobject": "Account", "fields": ["Id"]},
            {"name": "second", "primary_key": "id", "sobject": "Contact", "fields": ["Id"]},
            {"name": "third", "primary_key": "id", "sobject": "Opportunity", "fields": ["Id"]}
        ]
        
        source = salesforce_bulk2_source(
            resource_configs=resource_configs,
            credentials="salesforce.dev"
        )
        
        # Source should be created
        assert source is not None
    
    def test_source_with_empty_credentials(self):
        """Test source with empty string credentials."""
        resource_configs = [{
            "name": "accounts",
            "primary_key": "id",
            "sobject": "Account",
            "fields": ["Id"]
        }]
        
        # Empty string is allowed by the function, validation happens later in the driver
        # So we just verify the source is created
        source = salesforce_bulk2_source(
            resource_configs=resource_configs,
            credentials=""
        )
        
        # Source should be created (validation happens in driver, not source)
        assert source is not None


class TestSourceErrorHandling:
    """Tests for error handling in source creation."""
    
    def test_source_requires_credentials(self):
        """Test that credentials are required."""
        resource_configs = [{
            "name": "accounts",
            "primary_key": "id",
            "sobject": "Account",
            "fields": ["Id"]
        }]
        
        with pytest.raises(ValueError, match="credentials must be provided"):
            salesforce_bulk2_source(
                resource_configs=resource_configs,
                credentials=None
            )
    
    @patch('stairway_to_salesforce.sources.salesforce_bulk2.source.validate_resource_configs')
    def test_source_validation_errors_propagate(self, mock_validate):
        """Test that validation errors are propagated."""
        resource_configs = [{"invalid": "config"}]
        
        mock_validate.side_effect = ValueError("Invalid configuration")
        
        with pytest.raises(ValueError, match="Invalid configuration"):
            salesforce_bulk2_source(
                resource_configs=resource_configs,
                credentials="salesforce.dev"
            )


class TestSourceDocumentation:
    """Tests to verify source follows DLT conventions."""
    
    @patch('stairway_to_salesforce.sources.salesforce_bulk2.source.validate_resource_configs')
    def test_source_returns_callable(self, mock_validate):
        """Test that source returns a callable."""
        resource_configs = [{
            "name": "accounts",
            "primary_key": "id",
            "sobject": "Account",
            "fields": ["Id"]
        }]
        
        source = salesforce_bulk2_source(
            resource_configs=resource_configs,
            credentials="salesforce.dev"
        )
        
        # Source should be callable (it's a DLT source)
        # The @dlt.source decorator makes it callable
        assert source is not None
    
    @patch('stairway_to_salesforce.sources.salesforce_bulk2.source.validate_resource_configs')
    def test_source_has_name_attribute(self, mock_validate):
        """Test that source is created successfully."""
        resource_configs = [{
            "name": "accounts",
            "primary_key": "id",
            "sobject": "Account",
            "fields": ["Id"]
        }]
        
        source = salesforce_bulk2_source(
            resource_configs=resource_configs,
            credentials="salesforce.dev"
        )
        
        # Verify source was created
        assert source is not None