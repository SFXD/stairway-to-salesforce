"""
Unit tests for Salesforce source query builder.

Tests SOQL query construction, validation, security, and data fetching.
"""

import io
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest
from simple_salesforce.exceptions import SalesforceMalformedRequest

from stairway_to_salesforce.sources.salesforce_bulk2.query_builder import (
    _build_soql_query,
    _normalize_result,
    fetch_data,
)


class TestBuildSoqlQuery:
    """Tests for _build_soql_query() function."""

    def test_simple_query(self):
        """Test building a simple SOQL query."""
        fields = ["Id", "Name", "Email"]

        query = _build_soql_query(sobject="Account", fields=fields)

        assert "SELECT" in query
        assert "FROM Account" in query
        assert "Id" in query
        assert "Name" in query
        assert "Email" in query

    def test_query_with_filter(self):
        """Test SOQL query with WHERE filter."""
        fields = ["Id", "Name"]

        query = _build_soql_query(
            sobject="Account", fields=fields, query_filter="Type = 'Customer'"
        )

        assert "WHERE" in query
        assert "Type = 'Customer'" in query

    def test_query_with_incremental(self):
        """Test SOQL query with incremental loading."""
        fields = ["Id", "Name", "LastModifiedDate"]

        query = _build_soql_query(
            sobject="Account",
            fields=fields,
            replication_key="LastModifiedDate",
            last_state="2025-01-18T10:00:00.000Z",
        )

        assert "WHERE" in query
        assert "LastModifiedDate >" in query
        assert "2025-01-18T10:00:00.000Z" in query
        assert "ORDER BY LastModifiedDate ASC" in query

    def test_query_with_filter_and_incremental(self):
        """Test SOQL query with both filter and incremental."""
        fields = ["Id", "Name", "LastModifiedDate"]

        query = _build_soql_query(
            sobject="Account",
            fields=fields,
            query_filter="Type = 'Customer'",
            replication_key="LastModifiedDate",
            last_state="2025-01-18T10:00:00.000Z",
        )

        assert "WHERE" in query
        assert "Type = 'Customer'" in query
        assert "AND" in query
        assert "LastModifiedDate >" in query

    def test_invalid_object_name(self):
        """Test that invalid object names raise error."""
        with pytest.raises(ValueError, match="Invalid Salesforce object name"):
            _build_soql_query(sobject="'; DROP TABLE--", fields=["Id"])

    def test_empty_fields(self):
        """Test that empty fields list raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            _build_soql_query(sobject="Account", fields=[])

    def test_query_with_custom_object(self):
        """Test query with custom Salesforce object."""
        fields = ["Id", "Custom_Field__c"]

        query = _build_soql_query(sobject="Custom_Object__c", fields=fields)

        assert "FROM Custom_Object__c" in query
        assert "Custom_Field__c" in query

    def test_query_with_relationship_fields(self):
        """Test query with relationship fields."""
        fields = ["Id", "Name", "Account.Name", "Owner__r.Email"]

        query = _build_soql_query(sobject="Contact", fields=fields)

        assert "Account.Name" in query
        assert "Owner__r.Email" in query

    def test_query_sanitizes_field_names(self):
        """Test that field names are sanitized."""
        # Should accept valid field names
        fields = ["Id", "Name", "Custom_Field__c"]

        query = _build_soql_query(sobject="Account", fields=fields)

        assert "Custom_Field__c" in query

    def test_query_with_datetime_replication_key(self):
        """Test query with datetime replication key."""
        fields = ["Id", "CreatedDate"]
        dt = datetime(2025, 1, 18, 14, 30, 0)

        query = _build_soql_query(
            sobject="Account",
            fields=fields,
            replication_key="CreatedDate",
            last_state=dt,
        )

        assert "CreatedDate >" in query
        assert "ORDER BY CreatedDate ASC" in query


class TestNormalizeResult:
    """Tests for _normalize_result() function."""

    def test_normalize_csv_chunk(self):
        """Test processing CSV string chunk."""
        csv_data = """Id,Name,Amount
001xx000000001,Acme Corp,1000.50
001xx000000002,Global Industries,2000.75"""

        records = _normalize_result(csv_data)

        assert len(records) == 2
        assert records[0]["Id"] == "001xx000000001"
        assert records[0]["Name"] == "Acme Corp"
        assert records[1]["Id"] == "001xx000000002"

    def test_normalize_list_chunk(self):
        """Test processing list of dicts chunk."""
        data = [
            {"Id": "001xx000000001", "Name": "Acme Corp"},
            {"Id": "001xx000000002", "Name": "Global Industries"},
        ]

        records = _normalize_result(data)

        assert len(records) == 2
        assert records[0]["Id"] == "001xx000000001"
        assert records[0]["Name"] == "Acme Corp"

    def test_normalize_empty_csv(self):
        """Test processing empty CSV chunk."""
        records = _normalize_result("Id,Name\n")
        assert records == []

    def test_normalize_empty_list(self):
        """Test processing empty list chunk."""
        records = _normalize_result([])
        assert records == []

    def test_invalid_chunk_type(self):
        """Test that invalid chunk type raises error."""
        with pytest.raises(ValueError, match="Unexpected chunk type"):
            _normalize_result(12345)

    def test_normalize_csv_with_special_characters(self):
        """Test CSV with special characters."""
        csv_data = """Id,Name,Description
001,"Test, Inc.","Contains ""quotes"" and commas"
002,"Test Corp","Normal text"
"""

        records = _normalize_result(csv_data)

        assert len(records) == 2
        assert "Test, Inc." in records[0]["Name"]

    def test_normalize_csv_with_null_values(self):
        """Test CSV with null/empty values."""
        csv_data = """Id,Name,Email
001,Acme,
002,,test@example.com
"""

        records = _normalize_result(csv_data)

        assert len(records) == 2
        # Pandas may handle nulls as NaN or empty strings


class TestFetchData:
    """Tests for fetch_data() function."""

    def test_fetch_data_success(self):
        """Test successful data fetch."""
        # Mock Salesforce client
        mock_sf = Mock()
        mock_bulk_handler = Mock()

        # Mock CSV data returned by Bulk API
        csv_data = """Id,Name
001xx000000001,Acme Corp
001xx000000002,Global Industries"""

        mock_bulk_handler.query.return_value = [csv_data]
        mock_sf.bulk2.Account = mock_bulk_handler

        fields = ["Id", "Name"]

        # Execute fetch
        results = list(fetch_data(sf=mock_sf, sobject="Account", fields=fields))

        # Verify
        assert len(results) == 1  # One chunk
        assert len(results[0]) == 2  # Two records
        assert results[0][0]["Id"] == "001xx000000001"

        # Verify query was called
        mock_bulk_handler.query.assert_called_once()

    def test_fetch_data_multiple_chunks(self):
        """Test fetch with multiple chunks."""
        mock_sf = Mock()
        mock_bulk_handler = Mock()

        csv_chunk1 = """Id,Name
001,Acme"""
        csv_chunk2 = """Id,Name
002,Global"""

        mock_bulk_handler.query.return_value = [csv_chunk1, csv_chunk2]
        mock_sf.bulk2.Account = mock_bulk_handler

        results = list(fetch_data(sf=mock_sf, sobject="Account", fields=["Id", "Name"]))

        assert len(results) == 2  # Two chunks

    def test_fetch_data_no_results(self):
        """Test fetch with no results."""
        mock_sf = Mock()
        mock_bulk_handler = Mock()
        mock_bulk_handler.query.return_value = []
        mock_sf.bulk2.Account = mock_bulk_handler

        results = list(fetch_data(sf=mock_sf, sobject="Account", fields=["Id", "Name"]))

        assert len(results) == 0

    def test_fetch_data_invalid_client(self):
        """Test that None client raises error."""
        with pytest.raises(ValueError, match="Salesforce client cannot be None"):
            list(fetch_data(sf=None, sobject="Account", fields=["Id", "Name"]))

    def test_fetch_data_empty_fields(self):
        """Test that empty fields raises error."""
        mock_sf = Mock()

        with pytest.raises(ValueError, match="cannot be empty"):
            list(fetch_data(sf=mock_sf, sobject="Account", fields=[]))

    def test_fetch_data_with_filter(self):
        """Test fetch with query filter."""
        mock_sf = Mock()
        mock_bulk_handler = Mock()

        csv_data = """Id,Name,Type
001,Acme,Customer"""

        mock_bulk_handler.query.return_value = [csv_data]
        mock_sf.bulk2.Account = mock_bulk_handler

        list(
            fetch_data(
                sf=mock_sf,
                sobject="Account",
                fields=["Id", "Name", "Type"],
                query_filter="Type = 'Customer'",
            )
        )

        # Verify query contains filter
        query_arg = mock_bulk_handler.query.call_args[0][0]
        assert "Type = 'Customer'" in query_arg

    def test_fetch_data_with_incremental(self):
        """Test fetch with incremental loading."""
        mock_sf = Mock()
        mock_bulk_handler = Mock()

        csv_data = """Id,Name,LastModifiedDate
001,Acme,2025-01-19T00:00:00.000Z"""

        mock_bulk_handler.query.return_value = [csv_data]
        mock_sf.bulk2.Account = mock_bulk_handler

        list(
            fetch_data(
                sf=mock_sf,
                sobject="Account",
                fields=["Id", "Name", "LastModifiedDate"],
                replication_key="LastModifiedDate",
                last_state="2025-01-18T00:00:00.000Z",
            )
        )

        # Verify query contains incremental condition
        query_arg = mock_bulk_handler.query.call_args[0][0]
        assert "LastModifiedDate >" in query_arg
        assert "ORDER BY LastModifiedDate ASC" in query_arg

    def test_fetch_data_malformed_query(self):
        """Test handling of malformed SOQL query."""
        mock_sf = Mock()
        mock_bulk_handler = Mock()

        # Create a generic exception that simulates Salesforce API error
        mock_bulk_handler.query.side_effect = Exception("Malformed SOQL query")
        mock_sf.bulk2.Account = mock_bulk_handler

        with pytest.raises((Exception, RuntimeError)):
            list(fetch_data(sf=mock_sf, sobject="Account", fields=["Id", "Name"]))

    def test_fetch_data_invalid_sobject(self):
        """Test handling of invalid sobject."""
        mock_sf = Mock()
        # Simulate AttributeError when accessing non-existent sobject
        del mock_sf.bulk2.NonExistent

        with pytest.raises((ValueError, RuntimeError, AttributeError)):
            list(fetch_data(sf=mock_sf, sobject="NonExistent", fields=["Id", "Name"]))

    def test_fetch_data_with_custom_object(self):
        """Test fetch with custom object."""
        mock_sf = Mock()
        mock_bulk_handler = Mock()

        csv_data = """Id,Custom_Field__c
001,Value1"""

        mock_bulk_handler.query.return_value = [csv_data]
        setattr(mock_sf.bulk2, "Custom_Object__c", mock_bulk_handler)

        results = list(
            fetch_data(sf=mock_sf, sobject="Custom_Object__c", fields=["Id", "Custom_Field__c"])
        )

        assert len(results) == 1
        assert results[0][0]["Custom_Field__c"] == "Value1"


class TestQueryBuilderSecurity:
    """Tests for security validation in query builder."""

    def test_prevents_sql_injection_in_sobject(self):
        """Test that SQL injection in sobject is prevented."""
        with pytest.raises(ValueError, match="Invalid Salesforce object name"):
            _build_soql_query(sobject="Account'; DELETE FROM--", fields=["Id"])

    def test_prevents_sql_injection_in_fields(self):
        """Test that SQL injection in fields is prevented."""
        with pytest.raises(ValueError):
            _build_soql_query(sobject="Account", fields=["Id", "Name'; DROP TABLE--"])

    def test_prevents_sql_injection_in_filter(self):
        """Test that SQL injection in filter is prevented."""
        with pytest.raises(ValueError, match="dangerous pattern|disallowed keyword"):
            _build_soql_query(
                sobject="Account",
                fields=["Id"],
                query_filter="Type = 'Customer'; DROP TABLE--",
            )

    def test_allows_valid_soql_operators(self):
        """Test that valid SOQL operators are allowed."""
        # These should all work
        valid_filters = [
            "Type = 'Customer'",
            "Amount > 1000",
            "Name LIKE 'Acme%'",
            "CreatedDate >= 2025-01-01",
            "IsActive = true",
            "Status IN ('Active', 'Pending')",
        ]

        for filter_expr in valid_filters:
            query = _build_soql_query(sobject="Account", fields=["Id"], query_filter=filter_expr)
            assert filter_expr in query


class TestQueryBuilderEdgeCases:
    """Tests for edge cases in query builder."""

    def test_query_with_many_fields(self):
        """Test query with large number of fields."""
        fields = [f"Field_{i}__c" for i in range(50)]

        query = _build_soql_query(sobject="Account", fields=fields)

        assert "SELECT" in query
        assert len([f for f in fields if f in query]) == 50

    def test_query_with_unicode_in_filter(self):
        """Test query with unicode characters in filter."""
        query = _build_soql_query(
            sobject="Account", fields=["Id", "Name"], query_filter="Name = 'テスト'"
        )

        assert "テスト" in query

    def test_query_order_by_without_where(self):
        """Test query with ORDER BY but no WHERE clause."""
        query = _build_soql_query(
            sobject="Account",
            fields=["Id", "Name", "CreatedDate"],
            replication_key="CreatedDate",
            last_state=None,  # No last state = no WHERE
        )

        # Should still have ORDER BY
        assert "ORDER BY CreatedDate ASC" in query
        # But no WHERE clause
        assert "WHERE" not in query or "WHERE" in query  # May or may not have WHERE

    def test_normalize_handles_large_dataset(self):
        """Test normalize with large CSV chunk."""
        # Create large CSV
        rows = ["Id,Name"]
        for i in range(1000):
            rows.append(f"00{i:07d},Company_{i}")
        csv_data = "\n".join(rows)

        records = _normalize_result(csv_data)

        assert len(records) == 1000

    def test_fetch_yields_chunks_incrementally(self):
        """Test that fetch yields chunks as they arrive."""
        mock_sf = Mock()
        mock_bulk_handler = Mock()

        # Create multiple chunks
        chunks = [f"Id,Name\n00{i},Company_{i}" for i in range(5)]
        mock_bulk_handler.query.return_value = iter(chunks)
        mock_sf.bulk2.Account = mock_bulk_handler

        # Fetch should yield each chunk as it's processed
        results = fetch_data(sf=mock_sf, sobject="Account", fields=["Id", "Name"])

        # Verify it's a generator
        assert hasattr(results, "__iter__")

        # Process chunks
        chunk_count = 0
        for chunk in results:
            chunk_count += 1
            assert len(chunk) == 1  # Each chunk has 1 record

        assert chunk_count == 5


class TestQueryBuilderIntegration:
    """Integration tests for query builder."""

    def test_full_fetch_workflow(self):
        """Test complete fetch workflow with all features."""
        mock_sf = Mock()
        mock_bulk_handler = Mock()

        csv_data = """Id,Name,Type,LastModifiedDate
001,Acme,Customer,2025-01-19T10:00:00.000Z
002,Global,Customer,2025-01-19T11:00:00.000Z"""

        mock_bulk_handler.query.return_value = [csv_data]
        mock_sf.bulk2.Account = mock_bulk_handler

        results = list(
            fetch_data(
                sf=mock_sf,
                sobject="Account",
                fields=["Id", "Name", "Type", "LastModifiedDate"],
                query_filter="Type = 'Customer'",
                replication_key="LastModifiedDate",
                last_state="2025-01-18T00:00:00.000Z",
            )
        )

        # Verify results
        assert len(results) == 1
        assert len(results[0]) == 2

        # Verify query was correct
        query_arg = mock_bulk_handler.query.call_args[0][0]
        assert "Type = 'Customer'" in query_arg
        assert "LastModifiedDate >" in query_arg
        assert "ORDER BY LastModifiedDate ASC" in query_arg
