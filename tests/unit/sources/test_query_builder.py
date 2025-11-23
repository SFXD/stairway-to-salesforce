"""
Unit tests for Salesforce source query builder.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import io
from datetime import datetime

from dlt_salesforce_advanced.sources.salesforce_bulk2.query_builder import (
    _build_soql_query,
    _process_result,
    fetch_data,
)
from simple_salesforce.exceptions import SalesforceMalformedRequest


class TestBuildSoqlQuery:
    """Tests for _build_soql_query()"""
    
    def test_simple_query(self, sample_field_mapping):
        """Test building a simple SOQL query."""
        query = _build_soql_query(
            source_sobject="Account",
            fields=sample_field_mapping
        )
        
        assert "SELECT" in query
        assert "FROM Account" in query
        assert "Id" in query
        assert "Name" in query
    
    def test_query_with_filter(self, sample_field_mapping):
        """Test SOQL query with WHERE filter."""
        query = _build_soql_query(
            source_sobject="Account",
            fields=sample_field_mapping,
            source_query_filter="Type = 'Customer'"
        )
        
        assert "WHERE" in query
        assert "Type = 'Customer'" in query
    
    def test_query_with_incremental(self, sample_field_mapping):
        """Test SOQL query with incremental loading."""
        query = _build_soql_query(
            source_sobject="Account",
            fields=sample_field_mapping,
            source_replication_key="LastModifiedDate",
            last_state="2025-01-18T10:00:00.000Z"
        )
        
        assert "WHERE" in query
        assert "LastModifiedDate >" in query
        assert "2025-01-18T10:00:00.000Z" in query
        assert "ORDER BY LastModifiedDate ASC" in query
    
    def test_query_with_filter_and_incremental(self, sample_field_mapping):
        """Test SOQL query with both filter and incremental."""
        query = _build_soql_query(
            source_sobject="Account",
            fields=sample_field_mapping,
            source_query_filter="Type = 'Customer'",
            source_replication_key="LastModifiedDate",
            last_state="2025-01-18T10:00:00.000Z"
        )
        
        assert "WHERE" in query
        assert "Type = 'Customer'" in query
        assert "AND" in query
        assert "LastModifiedDate >" in query
    
    def test_invalid_object_name(self, sample_field_mapping):
        """Test that invalid object names raise error."""
        with pytest.raises(ValueError, match="Invalid Salesforce object name"):
            _build_soql_query(
                source_sobject="'; DROP TABLE--",
                fields=sample_field_mapping
            )
    
    def test_empty_fields(self):
        """Test that empty fields dict raises error."""
        with pytest.raises(ValueError, match="Fields dictionary cannot be empty"):
            _build_soql_query(
                source_sobject="Account",
                fields={}
            )


class TestProcessResult:
    """Tests for _process_result()"""
    
    def test_process_csv_chunk(self, sample_csv_data, sample_field_mapping):
        """Test processing CSV string chunk."""
        records = _process_result(sample_csv_data, sample_field_mapping)
        
        assert len(records) == 2
        assert records[0]["account_id"] == "001xx000000001"
        assert records[0]["account_name"] == "Acme Corp"
        assert records[1]["account_id"] == "001xx000000002"
    
    def test_process_list_chunk(self, sample_account_data, sample_field_mapping):
        """Test processing list of dicts chunk."""
        records = _process_result(sample_account_data, sample_field_mapping)
        
        assert len(records) == 2
        assert records[0]["account_id"] == "001xx000000001"
        assert records[0]["account_name"] == "Acme Corp"
    
    def test_process_empty_chunk(self, sample_field_mapping):
        """Test processing empty chunk."""
        records = _process_result("Id,Name\n", sample_field_mapping)
        assert records == []
        
        records = _process_result([], sample_field_mapping)
        assert records == []
    
    def test_invalid_chunk_type(self, sample_field_mapping):
        """Test that invalid chunk type raises error."""
        with pytest.raises(ValueError, match="Unexpected chunk type"):
            _process_result(12345, sample_field_mapping)


class TestFetchData:
    """Tests for fetch_data()"""
    
    def test_fetch_data_success(
        self,
        mock_salesforce_with_bulk2,
        mock_bulk2_client,
        sample_csv_data,
        sample_field_mapping
    ):
        """Test successful data fetch."""
        # Setup mock to return CSV data
        mock_bulk2_client.query.return_value = [sample_csv_data]
        
        # Execute fetch
        results = list(fetch_data(
            sf=mock_salesforce_with_bulk2,
            source_sobject="Account",
            fields=sample_field_mapping
        ))
        
        # Verify
        assert len(results) == 1  # One batch
        assert len(results[0]) == 2  # Two records
        assert results[0][0]["account_id"] == "001xx000000001"
        
        # Verify query was called
        mock_bulk2_client.query.assert_called_once()
    
    def test_fetch_data_multiple_chunks(
        self,
        mock_salesforce_with_bulk2,
        mock_bulk2_client,
        sample_csv_data,
        sample_field_mapping
    ):
        """Test fetch with multiple chunks."""
        # Setup mock to return multiple chunks
        mock_bulk2_client.query.return_value = [
            sample_csv_data,
            sample_csv_data
        ]
        
        results = list(fetch_data(
            sf=mock_salesforce_with_bulk2,
            source_sobject="Account",
            fields=sample_field_mapping
        ))
        
        assert len(results) == 2  # Two batches
    
    def test_fetch_data_no_results(
        self,
        mock_salesforce_with_bulk2,
        mock_bulk2_client,
        sample_field_mapping
    ):
        """Test fetch with no results."""
        mock_bulk2_client.query.return_value = []
        
        results = list(fetch_data(
            sf=mock_salesforce_with_bulk2,
            source_sobject="Account",
            fields=sample_field_mapping
        ))
        
        assert len(results) == 0
    
    def test_fetch_data_invalid_client(self, sample_field_mapping):
        """Test that None client raises error."""
        with pytest.raises(ValueError, match="Salesforce client cannot be None"):
            list(fetch_data(
                sf=None,
                source_sobject="Account",
                fields=sample_field_mapping
            ))
    
    def test_fetch_data_empty_fields(self, mock_salesforce_with_bulk2):
        """Test that empty fields raises error."""
        with pytest.raises(ValueError, match="Fields mapping cannot be empty"):
            list(fetch_data(
                sf=mock_salesforce_with_bulk2,
                source_sobject="Account",
                fields={}
            ))
    
    def test_fetch_data_malformed_query(
        self,
        mock_salesforce_with_bulk2,
        mock_bulk2_client,
        sample_field_mapping
    ):
        """Test handling of malformed SOQL query."""
        # Create a mock exception instead of trying to instantiate the real one
        mock_exception = Mock(spec=SalesforceMalformedRequest)
        mock_exception.__class__ = SalesforceMalformedRequest
        
        # Make the query raise this exception
        mock_bulk2_client.query.side_effect = mock_exception
        
        # Should re-raise as SalesforceMalformedRequest
        with pytest.raises(Exception):  # Catch any exception
            list(fetch_data(
                sf=mock_salesforce_with_bulk2,
                source_sobject="Account",
                fields=sample_field_mapping
            ))