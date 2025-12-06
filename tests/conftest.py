"""
Shared pytest fixtures for Salesforce tests.

This module provides common fixtures used across all test modules.
"""

import pytest
from unittest.mock import Mock
from pathlib import Path
import tempfile
import os
from datetime import datetime

from simple_salesforce import Salesforce
from dlt_salesforce_advanced.drivers.salesforce_driver.sfdriver import (
    SecurityTokenAuth,
    ConsumerKeySecretDomainAuth,
)

# ============================================================================
# Credential Fixtures
# ============================================================================

@pytest.fixture
def mock_security_token_credentials():
    """Mock SecurityTokenAuth credentials."""
    return SecurityTokenAuth(
        user_name="test@example.com",
        password="test_password",
        security_token="test_token"
    )


@pytest.fixture
def mock_consumer_key_credentials():
    """Mock ConsumerKeySecretDomainAuth credentials."""
    return ConsumerKeySecretDomainAuth(
        consumer_key="test_consumer_key",
        consumer_secret="test_consumer_secret",
        domain="test"
    )


@pytest.fixture
def mock_credentials_dict():
    """Mock credentials as dictionary (for testing resolution)."""
    return {
        "user_name": "test@example.com",
        "password": "test_password",
        "security_token": "test_token"
    }


# ============================================================================
# Salesforce Client Fixtures
# ============================================================================
@pytest.fixture
def mock_salesforce_client():
    """Mock Salesforce client."""
    mock_sf = Mock(spec=Salesforce)
    mock_sf.bulk2 = Mock()
    return mock_sf


@pytest.fixture
def mock_bulk2_client():
    """Mock Bulk API v2 client."""
    mock_client = Mock()
    mock_client.query = Mock(return_value=[])
    mock_client.insert = Mock(return_value=[])
    mock_client.upsert = Mock(return_value=[])
    mock_client.delete = Mock(return_value=[])
    mock_client.get_failed_records = Mock(return_value=None)
    mock_client.get_successful_records = Mock(return_value=None)
    return mock_client


@pytest.fixture
def mock_salesforce_with_bulk2(mock_salesforce_client, mock_bulk2_client):
    """Mock Salesforce client with Bulk2 API."""
    # Setup bulk2.Account, bulk2.Contact, etc.
    mock_salesforce_client.bulk2.Account = mock_bulk2_client
    mock_salesforce_client.bulk2.Contact = mock_bulk2_client
    return mock_salesforce_client


# ============================================================================
# Data Fixtures
# ============================================================================

@pytest.fixture
def sample_account_data():
    """Sample Account records."""
    return [
        {
            "Id": "001xx000000001",
            "Name": "Acme Corp",
            "LastModifiedDate": "2025-01-18T10:00:00.000Z",
            "Website": "https://acme.com"
        },
        {
            "Id": "001xx000000002",
            "Name": "Global Industries",
            "LastModifiedDate": "2025-01-18T11:00:00.000Z",
            "Website": "https://global.com"
        }
    ]


@pytest.fixture
def sample_field_mapping():
    """Sample field mapping configuration."""
    return {
        "Id": "account_id",
        "Name": "account_name",
        "LastModifiedDate": "modified_at",
        "Website": "website"
    }


@pytest.fixture
def sample_csv_data():
    """Sample CSV data as string."""
    return """Id,Name,LastModifiedDate,Website
001xx000000001,Acme Corp,2025-01-18T10:00:00.000Z,https://acme.com
001xx000000002,Global Industries,2025-01-18T11:00:00.000Z,https://global.com"""


@pytest.fixture
def sample_resource_config():
    """Sample resource configuration."""
    return {
        "target_name": "tb_accounts",
        "target_primary_key": "account_id",
        "source_sobject": "Account",
        "write_disposition": "merge",
        "fields": {
            "Id": "account_id",
            "Name": "account_name",
            "LastModifiedDate": "modified_at"
        },
        "source_replication_key": "LastModifiedDate"
    }


# ============================================================================
# File Fixtures
# ============================================================================

@pytest.fixture
def temp_csv_file(sample_csv_data):
    """Create a temporary CSV file."""
    temp_file = tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.csv',
        delete=False,
        newline='',
        encoding='utf-8'
    )
    temp_file.write(sample_csv_data)
    temp_file.close()
    
    yield temp_file.name
    
    # Cleanup
    try:
        os.unlink(temp_file.name)
    except Exception:
        pass


@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    
    # Cleanup
    import shutil
    try:
        shutil.rmtree(temp_path)
    except Exception:
        pass


# ============================================================================
# Job Result Fixtures
# ============================================================================

@pytest.fixture
def successful_job_result():
    """Mock successful Bulk API job result."""
    return [{
        'job_id': '750xx000000TEST',
        'numberRecordsProcessed': 100,
        'numberRecordsFailed': 0
    }]


@pytest.fixture
def failed_job_result():
    """Mock failed Bulk API job result."""
    return [{
        'job_id': '750xx000000FAIL',
        'numberRecordsProcessed': 100,
        'numberRecordsFailed': 5
    }]


@pytest.fixture
def partial_success_job_result():
    """Mock partially successful Bulk API job result."""
    return [{
        'job_id': '750xx000000PART',
        'numberRecordsProcessed': 100,
        'numberRecordsFailed': 10
    }]


@pytest.fixture
def sample_failed_records_csv():
    """Sample failed records CSV from Salesforce."""
    return """Id,Name,sf__Error
001xx000000003,Bad Record,"DUPLICATE_VALUE:duplicate value found: Email__c duplicates value on record with id: 001xx000000001"
001xx000000004,Invalid Record,"REQUIRED_FIELD_MISSING:Required fields are missing: [Name]"
"""


# ============================================================================
# DateTime Fixtures
# ============================================================================

@pytest.fixture
def fixed_datetime():
    """Fixed datetime for testing."""
    return datetime(2025, 1, 18, 14, 30, 0)


@pytest.fixture
def mock_datetime(monkeypatch, fixed_datetime):
    """Mock datetime.now() to return fixed datetime."""
    class MockDatetime:
        @staticmethod
        def now():
            return fixed_datetime
        
        @staticmethod
        def strftime(fmt):
            return fixed_datetime.strftime(fmt)
    
    monkeypatch.setattr("datetime.datetime", MockDatetime)
    return fixed_datetime