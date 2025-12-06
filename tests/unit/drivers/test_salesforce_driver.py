"""
Unit tests for Salesforce driver and credential resolution.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from dlt_salesforce_advanced.drivers.salesforce_driver.sfdriver import (
    resolve_salesforce_credentials,
    make_salesforce_driver,
    SecurityTokenAuth,
    ConsumerKeySecretDomainAuth,
    OrganizationIdAuth,
    ConsumerKeySecretAuth,
    JWTAuth,
    InstanceAuth,
)


class TestResolveSalesforceCredentials:
    """Tests for resolve_salesforce_credentials()"""
    
    def test_resolve_already_resolved_credentials(self, mock_security_token_credentials):
        """Test that already resolved credentials are returned as-is."""
        result = resolve_salesforce_credentials(mock_security_token_credentials)
        assert result == mock_security_token_credentials
        assert isinstance(result, SecurityTokenAuth)
    
    def test_resolve_from_dict_security_token(self):
        """Test resolution from dict to SecurityTokenAuth."""
        cred_dict = {
            "user_name": "test@example.com",
            "password": "test_password",
            "security_token": "test_token"
        }
        
        result = resolve_salesforce_credentials(cred_dict)
        
        assert isinstance(result, SecurityTokenAuth)
        assert result.user_name == "test@example.com"
    
    def test_resolve_from_dict_consumer_key_domain(self):
        """Test resolution from dict to ConsumerKeySecretDomainAuth."""
        cred_dict = {
            "consumer_key": "test_key",
            "consumer_secret": "test_secret",
            "domain": "test"
        }
        
        result = resolve_salesforce_credentials(cred_dict)
        
        assert isinstance(result, ConsumerKeySecretDomainAuth)
    
    def test_resolve_from_string_path(self):
        """Test resolution from DLT secrets path."""
        # Mock the entire dlt.secrets object
        mock_creds_dict = {
            "user_name": "test@example.com",
            "password": "test_password",
            "security_token": "test_token"
        }
        
        with patch('dlt_salesforce_advanced.drivers.salesforce_driver.dlt') as mock_dlt:
            # Setup the mock to return credentials when accessed like a dict
            mock_dlt.secrets.__getitem__.return_value = mock_creds_dict
            
            result = resolve_salesforce_credentials("salesforce.dev")
            
            assert isinstance(result, SecurityTokenAuth)
            mock_dlt.secrets.__getitem__.assert_called_once_with("salesforce.dev")
    
    def test_resolve_invalid_dict(self):
        """Test that invalid dict raises error."""
        cred_dict = {"invalid": "credentials"}
        
        with pytest.raises(ValueError, match="Could not determine Salesforce credential type"):
            resolve_salesforce_credentials(cred_dict)
    
    def test_resolve_invalid_type(self):
        """Test that invalid type raises TypeError."""
        with pytest.raises(TypeError, match="must be a SalesforceDriverAuth instance"):
            resolve_salesforce_credentials(123)


class TestMakeSalesforceDriver:
    """Tests for make_salesforce_driver()"""
    
    @patch('dlt_salesforce_advanced.drivers.salesforce_driver.Salesforce')
    def test_make_driver_with_security_token(self, mock_sf_class, mock_security_token_credentials):
        """Test driver creation with SecurityTokenAuth."""
        mock_sf_instance = Mock()
        mock_sf_class.return_value = mock_sf_instance
        
        result = make_salesforce_driver(mock_security_token_credentials)
        
        assert result == mock_sf_instance
        mock_sf_class.assert_called_once()
        call_kwargs = mock_sf_class.call_args[1]
        assert call_kwargs['username'] == "test@example.com"
    
    @patch('dlt_salesforce_advanced.drivers.salesforce_driver.Salesforce')
    def test_make_driver_with_consumer_key(self, mock_sf_class, mock_consumer_key_credentials):
        """Test driver creation with ConsumerKeySecretDomainAuth."""
        mock_sf_instance = Mock()
        mock_sf_class.return_value = mock_sf_instance
        
        result = make_salesforce_driver(mock_consumer_key_credentials)
        
        assert result == mock_sf_instance
        mock_sf_class.assert_called_once()
    
    @patch('dlt_salesforce_advanced.drivers.salesforce_driver.Salesforce')
    def test_make_driver_resolves_dict_credentials(self, mock_sf_class):
        """Test that dict credentials are resolved before driver creation."""
        mock_sf_instance = Mock()
        mock_sf_class.return_value = mock_sf_instance
        
        cred_dict = {
            "user_name": "test@example.com",
            "password": "test_password",
            "security_token": "test_token"
        }
        
        result = make_salesforce_driver(cred_dict)
        
        assert result == mock_sf_instance
        mock_sf_class.assert_called_once()