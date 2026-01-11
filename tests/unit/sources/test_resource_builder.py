"""
Unit tests for DLT resource builder.
"""

import pytest
from unittest.mock import Mock, patch

from dlt_salesforce_advanced.sources.salesforce_bulk2.resource_builder import (
    validate_resource_configs,
    build_resource,
)


class TestValidateResourceConfigs:
    """Tests for validate_resource_configs()"""
    
    def test_validate_valid_configs(self, sample_resource_config):
        """Test validation of valid resource configs."""
        configs = [sample_resource_config]
        validate_resource_configs(configs)  # Should not raise
    
    def test_validate_empty_configs(self):
        """Test that empty configs raises error."""
        with pytest.raises(ValueError, match="At least one resource configuration is required"):
            validate_resource_configs([])
    
    def test_validate_missing_required_fields(self):
        """Test that missing required fields raises error."""
        configs = [{
            "target_name": "accounts"
            # Missing target_primary_key and source_sobject
        }]
        
        with pytest.raises(ValueError, match="missing required fields"):
            validate_resource_configs(configs)
    
    def test_validate_invalid_write_disposition(self, sample_resource_config):
        """Test that invalid write_disposition raises error."""
        config = sample_resource_config.copy()
        config["write_disposition"] = "invalid"
        
        with pytest.raises(ValueError, match="must be one of"):
            validate_resource_configs([config])
    
    def test_validate_replication_key_not_in_fields(self, sample_resource_config):
        """Test that replication key must exist in fields."""
        config = sample_resource_config.copy()
        config["source_replication_key"] = "NonExistentField"
        
        with pytest.raises(ValueError, match="must exist in fields dictionary"):
            validate_resource_configs([config])


class TestBuildResource:
    """Tests for build_resource()"""
    
    @patch('dlt_salesforce_advanced.drivers.salesforce_driver.sfdriver.get_salesforce_driver')
    def test_build_resource_success(
        self,
        mock_resolve,
        sample_resource_config,
        mock_security_token_credentials
    ):
        """Test successful resource building."""
        mock_resolve.return_value = mock_security_token_credentials
        mock_fetch_fn = Mock()
        
        resource = build_resource(
            config=sample_resource_config,
            fetch_data_fn=mock_fetch_fn,
            credentials=mock_security_token_credentials,
            session=None
        )
        
        # Verify resource was created
        assert callable(resource)