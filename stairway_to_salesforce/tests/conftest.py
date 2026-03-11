"""
Shared pytest fixtures for Salesforce tests.

This module provides common fixtures used across all test modules,
with special focus on supporting source module tests.
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
from simple_salesforce import Salesforce

from stairway_to_salesforce.drivers.salesforce_driver.sfdriver_specs import (
    ConsumerKeySecretDomainAuth,
    SecurityTokenAuth,
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
        security_token="test_token",
    )


@pytest.fixture
def mock_consumer_key_credentials():
    """Mock ConsumerKeySecretDomainAuth credentials."""
    return ConsumerKeySecretDomainAuth(
        consumer_key="test_consumer_key",
        consumer_secret="test_consumer_secret",
        domain="test",
    )


@pytest.fixture
def mock_credentials_dict():
    """Mock credentials as dictionary (for testing resolution)."""
    return {
        "user_name": "test@example.com",
        "password": "test_password",
        "security_token": "test_token",
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
    """Mock Bulk API v2 client for a specific object."""
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
    """Mock Salesforce client with Bulk2 API configured."""
    # Setup bulk2.Account, bulk2.Contact, etc.
    mock_salesforce_client.bulk2.Account = mock_bulk2_client
    mock_salesforce_client.bulk2.Contact = mock_bulk2_client
    mock_salesforce_client.bulk2.Opportunity = mock_bulk2_client

    # Support custom objects dynamically
    def get_bulk_handler(name):
        if not name.startswith("_"):
            return mock_bulk2_client
        raise AttributeError(f"No such attribute: {name}")

    mock_salesforce_client.bulk2.__getattr__ = get_bulk_handler

    return mock_salesforce_client


# ============================================================================
# Data Fixtures for Source Tests
# ============================================================================


@pytest.fixture
def sample_account_data():
    """Sample Account records as list of dicts."""
    return [
        {
            "Id": "001xx000000001",
            "Name": "Acme Corp",
            "Type": "Customer",
            "LastModifiedDate": "2025-01-18T10:00:00.000Z",
            "Website": "https://acme.com",
        },
        {
            "Id": "001xx000000002",
            "Name": "Global Industries",
            "Type": "Customer",
            "LastModifiedDate": "2025-01-18T11:00:00.000Z",
            "Website": "https://global.com",
        },
    ]


@pytest.fixture
def sample_contact_data():
    """Sample Contact records as list of dicts."""
    return [
        {
            "Id": "003xx000000001",
            "FirstName": "John",
            "LastName": "Doe",
            "Email": "john.doe@example.com",
            "AccountId": "001xx000000001",
        },
        {
            "Id": "003xx000000002",
            "FirstName": "Jane",
            "LastName": "Smith",
            "Email": "jane.smith@example.com",
            "AccountId": "001xx000000002",
        },
    ]


@pytest.fixture
def sample_field_list():
    """Sample field list for queries."""
    return ["Id", "Name", "Email", "Website"]


@pytest.fixture
def sample_csv_data():
    """Sample CSV data as string (Bulk API format)."""
    return """Id,Name,Type,LastModifiedDate,Website
001xx000000001,Acme Corp,Customer,2025-01-18T10:00:00.000Z,https://acme.com
001xx000000002,Global Industries,Customer,2025-01-18T11:00:00.000Z,https://global.com"""


@pytest.fixture
def sample_csv_with_nulls():
    """Sample CSV data with null values."""
    return """Id,Name,Email,Website
001xx000000001,Acme Corp,,https://acme.com
001xx000000002,Global Industries,info@global.com,
001xx000000003,Test Inc,,,"""


@pytest.fixture
def sample_resource_config():
    """Sample resource configuration for source."""
    return {
        "name": "accounts",
        "primary_key": "account_id",
        "sobject": "Account",
        "fields": ["Id", "Name", "Type", "LastModifiedDate"],
        "write_disposition": "append",
        "replication_key": "LastModifiedDate",
    }


@pytest.fixture
def sample_resource_configs():
    """Sample multiple resource configurations."""
    return [
        {
            "name": "accounts",
            "primary_key": "id",
            "sobject": "Account",
            "fields": ["Id", "Name", "Type"],
        },
        {
            "name": "contacts",
            "primary_key": "id",
            "sobject": "Contact",
            "fields": ["Id", "FirstName", "LastName", "Email"],
        },
    ]


# ============================================================================
# File Fixtures
# ============================================================================


@pytest.fixture
def temp_csv_file(sample_csv_data):
    """Create a temporary CSV file with sample data."""
    temp_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8"
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
# Job Result Fixtures (for destination tests)
# ============================================================================


@pytest.fixture
def successful_job_result():
    """Mock successful Bulk API job result."""
    return [
        {
            "job_id": "750xx000000TEST",
            "numberRecordsProcessed": 100,
            "numberRecordsFailed": 0,
        }
    ]


@pytest.fixture
def failed_job_result():
    """Mock failed Bulk API job result."""
    return [
        {
            "job_id": "750xx000000FAIL",
            "numberRecordsProcessed": 100,
            "numberRecordsFailed": 5,
        }
    ]


@pytest.fixture
def partial_success_job_result():
    """Mock partially successful Bulk API job result."""
    return [
        {
            "job_id": "750xx000000PART",
            "numberRecordsProcessed": 100,
            "numberRecordsFailed": 10,
        }
    ]


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

        @classmethod
        def fromisoformat(cls, date_string):
            return datetime.fromisoformat(date_string)

    monkeypatch.setattr("datetime.datetime", MockDatetime)
    return fixed_datetime


# ============================================================================
# Query Builder Fixtures
# ============================================================================


@pytest.fixture
def sample_soql_query():
    """Sample SOQL query string."""
    return "SELECT Id, Name, Email FROM Account WHERE Type = 'Customer' ORDER BY LastModifiedDate ASC LIMIT 2"


@pytest.fixture
def sample_bulk_query_response():
    """Sample response from Bulk API query (CSV format)."""
    return [
        """Id,Name,Email
001xx000000001,Acme Corp,info@acme.com
001xx000000002,Global Industries,contact@global.com"""
    ]


@pytest.fixture
def sample_bulk_query_multi_chunk():
    """Sample multi-chunk response from Bulk API query."""
    return [
        """Id,Name,Email
001,Acme,info@acme.com
002,Global,contact@global.com""",
        """Id,Name,Email
003,Test Inc,test@test.com
004,Sample Co,info@sample.com""",
    ]


# ============================================================================
# Resource Builder Fixtures
# ============================================================================


@pytest.fixture
def sample_incremental_config():
    """Sample resource config with incremental loading."""
    return {
        "name": "accounts_incremental",
        "primary_key": "id",
        "sobject": "Account",
        "fields": ["Id", "Name", "LastModifiedDate"],
        "write_disposition": "append",
        "replication_key": "LastModifiedDate",
    }


@pytest.fixture
def sample_filtered_config():
    """Sample resource config with query filter."""
    return {
        "name": "customer_accounts",
        "primary_key": "id",
        "sobject": "Account",
        "fields": ["Id", "Name", "Type"],
        "write_disposition": "append",
        "query_filter": "Type = 'Customer'",
    }


@pytest.fixture
def sample_custom_object_config():
    """Sample resource config for custom object."""
    return {
        "name": "custom_records",
        "primary_key": "id",
        "sobject": "Custom_Object__c",
        "fields": ["Id", "Name", "Custom_Field__c"],
    }


# ============================================================================
# Mock Functions for Source Tests
# ============================================================================


@pytest.fixture
def mock_fetch_data_function():
    """Mock fetch_data function for resource builder tests."""

    def fetch_mock(sf, sobject, fields, **kwargs):
        # Yield sample data
        yield [{"Id": "001", "Name": "Test 1"}, {"Id": "002", "Name": "Test 2"}]

    return Mock(side_effect=fetch_mock)


@pytest.fixture
def mock_fetch_data_empty():
    """Mock fetch_data function that returns no data."""

    def fetch_mock(sf, sobject, fields, **kwargs):
        return iter([])

    return Mock(side_effect=fetch_mock)


@pytest.fixture
def mock_fetch_data_error():
    """Mock fetch_data function that raises an error."""

    def fetch_mock(sf, sobject, fields, **kwargs):
        raise RuntimeError("Fetch failed")

    return Mock(side_effect=fetch_mock)


# ============================================================================
# Helper Functions
# ============================================================================


def create_mock_bulk_handler(query_response):
    """
    Helper to create a mock Bulk2 handler with query response.

    Args:
        query_response: List of CSV strings or list of dicts

    Returns:
        Mock Bulk2 handler
    """
    mock_handler = Mock()
    mock_handler.query = Mock(return_value=query_response)
    return mock_handler


def create_mock_salesforce_with_data(sobject_name, query_response):
    """
    Helper to create a mock Salesforce client with data for a specific object.

    Args:
        sobject_name: Name of the Salesforce object (e.g., "Account")
        query_response: Data to return from query

    Returns:
        Mock Salesforce client
    """
    mock_sf = Mock(spec=Salesforce)
    mock_handler = create_mock_bulk_handler(query_response)

    # Set up bulk2 attribute
    mock_sf.bulk2 = Mock()
    setattr(mock_sf.bulk2, sobject_name, mock_handler)

    return mock_sf


# Export helper functions as fixtures
@pytest.fixture
def create_mock_bulk_handler_fixture():
    """Fixture version of create_mock_bulk_handler."""
    return create_mock_bulk_handler


@pytest.fixture
def create_mock_salesforce_with_data_fixture():
    """Fixture version of create_mock_salesforce_with_data."""
    return create_mock_salesforce_with_data
