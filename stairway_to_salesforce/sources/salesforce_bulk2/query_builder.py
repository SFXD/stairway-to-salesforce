"""
SOQL query building and data fetching for Salesforce Bulk API v2.

This module handles all SOQL query construction, validation, security checks,
and data fetching from Salesforce using the Bulk API v2.
"""

from typing import Optional, Iterable, Any
from simple_salesforce.exceptions import SalesforceMalformedRequest
from simple_salesforce import Salesforce
from dlt.common.typing import TDataItem

import io
import pandas as pd

# Import shared validators
from stairway_to_salesforce.utils.salesforce_validators import (
    sanitize_sobject_name,
    sanitize_field_name,
    validate_soql_filter,
    format_soql_value,
)


def _build_soql_query(
    source_sobject: str,
    fields: dict[str, str],
    source_query_filter: Optional[str] = None,
    source_replication_key: Optional[str] = None,
    last_state: Optional[Any] = None
) -> str:
    """
    Build a secure SOQL query with proper validation and escaping.
    
    Args:
        source_sobject: Salesforce object name
        fields: Dictionary of source field names to target field names
        source_query_filter: Optional WHERE clause filter (will be validated)
        source_replication_key: Field used for incremental loading
        last_state: Last loaded value for incremental loading
    
    Returns:
        Complete SOQL query string
    
    Raises:
        ValueError: If inputs are invalid or potentially malicious
    """
    # Validate and sanitize object name
    source_sobject = sanitize_sobject_name(source_sobject)
    
    # Validate and sanitize all field names (allow relationship notation)
    if not fields:
        raise ValueError("Fields dictionary cannot be empty")
    
    source_fields = [sanitize_field_name(field) for field in fields.keys()]
    
    # Build WHERE clause
    predicates = []
    
    # Validate and add filter if present
    if source_query_filter:
        validate_soql_filter(source_query_filter)
        predicates.append(f"({source_query_filter})")
    
    # Build incremental predicate with proper escaping
    if source_replication_key and last_state is not None:
        # Validate replication key
        source_replication_key = sanitize_field_name(source_replication_key)
        
        # Format the value - assume datetime for replication keys
        formatted_value = format_soql_value(last_state, field_type="datetime")
        predicates.append(f"{source_replication_key} > {formatted_value}")
    
    # Construct WHERE clause
    where_clause = ""
    if predicates:
        where_clause = f" WHERE {' AND '.join(predicates)}"
    
    # Build ORDER BY clause
    order_by_clause = ""
    if source_replication_key:
        order_by_clause = f" ORDER BY {sanitize_field_name(source_replication_key)} ASC"
    
    # Construct final query
    query = f"SELECT {', '.join(source_fields)} FROM {source_sobject}{where_clause}{order_by_clause}"
    
    return query


def _process_result(chunk: Any, fields: dict[str, str]) -> Iterable[TDataItem]:
    """
    Process a chunk of results from Salesforce Bulk API.
    
    Args:
        chunk: Result chunk (CSV string or list of records)
        fields: Field mapping for renaming columns
    
    Returns:
        List of processed records as dictionaries
    
    Raises:
        ValueError: If chunk format is unexpected
    """
    # Handle different chunk types from Bulk API
    if isinstance(chunk, str):
        # CSV string response
        try:
            df = pd.read_csv(io.StringIO(chunk))
        except Exception as e:
            raise ValueError(f"Failed to parse CSV chunk: {str(e)}") from e
    
    elif isinstance(chunk, list):
        # List of dictionaries response
        if not chunk:
            return []
        df = pd.DataFrame(chunk)
    
    else:
        raise ValueError(
            f"Unexpected chunk type: {type(chunk).__name__}. "
            f"Expected str (CSV) or list (records)"
        )
    
    # Handle empty results
    if df.empty:
        return []
    
    # Rename columns based on field mapping
    rename_map = {
        source: target
        for source, target in fields.items()
        if source in df.columns
    }
    
    if rename_map:
        df.rename(columns=rename_map, inplace=True)
    
    # Convert to list of dictionaries
    return df.to_dict(orient="records")


def fetch_data(
    sf: Salesforce,
    source_sobject: str,
    fields: dict[str, str],
    source_replication_key: Optional[str] = None,
    last_state: Optional[Any] = None,
    source_query_filter: Optional[str] = None,
) -> Iterable[TDataItem]:
    """
    Fetch data from Salesforce using Bulk API v2.
    
    All SOQL query validation and security checks are performed here.
    
    Args:
        sf: Authenticated Salesforce client
        source_sobject: Salesforce object name (e.g., 'Account', 'Contact')
        fields: Dictionary mapping source field names to target field names
        source_replication_key: Optional field name for incremental loading
        last_state: Optional last loaded value for incremental loading
        source_query_filter: Optional SOQL WHERE clause filter (will be validated)
    
    Yields:
        Batches of records as lists of dictionaries
    
    Raises:
        ValueError: If inputs are invalid or contain security issues
        SalesforceMalformedRequest: If SOQL query is malformed
        RuntimeError: If Salesforce API request fails
    """
    # Validate inputs
    if not sf:
        raise ValueError("Salesforce client cannot be None")
    
    if not fields:
        raise ValueError("Fields mapping cannot be empty")
    
    # Build SOQL query with all security validations
    try:
        soql_query = _build_soql_query(
            source_sobject,
            fields,
            source_query_filter,
            source_replication_key,
            last_state
        )
    except ValueError as e:
        raise ValueError(f"Failed to build SOQL query: {str(e)}") from e
    
    # Log the query for debugging
    print(f"Executing SOQL: {soql_query}")
    
    # Execute bulk query
    try:
        bulk_handler = getattr(sf.bulk2, source_sobject)
        
        chunk_count = 0
        total_records = 0
        
        for chunk in bulk_handler.query(soql_query):
            chunk_count += 1
            
            try:
                records = _process_result(chunk, fields)
            except Exception as e:
                raise RuntimeError(
                    f"Failed to process chunk {chunk_count} for {source_sobject}: {str(e)}"
                ) from e
            
            if records:
                total_records += len(records)
                yield records
        
        if chunk_count == 0:
            print(f"No data returned for {source_sobject}")
        else:
            print(f"Successfully fetched {total_records} records from {source_sobject} in {chunk_count} chunks")
    
    except SalesforceMalformedRequest as e:
        raise SalesforceMalformedRequest(
            f"Malformed SOQL query for {source_sobject}. "
            f"Query: {soql_query}. "
            f"Error: {str(e)}"
        ) from e
    
    except AttributeError as e:
        raise ValueError(
            f"Invalid Salesforce object: '{source_sobject}'. "
            f"Ensure the object exists and you have permission to access it."
        ) from e
    
    except Exception as e:
        raise RuntimeError(
            f"Failed to fetch data from {source_sobject}: {str(e)}"
        ) from e