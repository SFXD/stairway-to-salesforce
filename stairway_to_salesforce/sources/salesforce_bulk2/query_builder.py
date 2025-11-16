"""
SOQL query building and data fetching for Salesforce Bulk API v2.

This module handles all SOQL query construction, validation, security checks,
and data fetching from Salesforce using the Bulk API v2.
"""

from typing import Optional, Iterable, Any
from datetime import datetime, date
from simple_salesforce.exceptions import SalesforceMalformedRequest
from simple_salesforce import Salesforce
from dlt.common.typing import TDataItem

import io
import pandas as pd
import re


def _sanitize_field_name(field_name: str) -> str:
    """
    Validate and sanitize SOQL field names to prevent injection.
    
    Args:
        field_name: Field name to validate
    
    Returns:
        Validated field name
    
    Raises:
        ValueError: If field name is invalid or potentially malicious
    """
    if not field_name:
        raise ValueError("Field name cannot be empty")
    
    # SOQL field names can contain: letters, numbers, underscores, dots (for relationships)
    # They must start with a letter
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)*$'
    if not re.match(pattern, field_name):
        raise ValueError(
            f"Invalid field name: '{field_name}'. "
            f"Field names must start with a letter and contain only letters, numbers, underscores, and dots."
        )
    
    # Additional security: block SQL/SOQL keywords that shouldn't be in field names
    dangerous_keywords = {'DROP', 'DELETE', 'INSERT', 'UPDATE', 'TRUNCATE', 'ALTER', 'EXEC'}
    # Split field_name by dot for relationship notation, then by underscore to tokenize
    tokens = []
    for part in field_name.upper().split('.'):
        tokens.extend(part.split('_'))
    
    if any(token in dangerous_keywords for token in tokens):
        raise ValueError(f"Field name contains disallowed keyword: '{field_name}'")
    
    return field_name


def _sanitize_sobject_name(sobject_name: str) -> str:
    """
    Validate and sanitize Salesforce object names.
    
    Args:
        sobject_name: Object name to validate
    
    Returns:
        Validated object name
    
    Raises:
        ValueError: If object name is invalid
    """
    if not sobject_name:
        raise ValueError("Object name cannot be empty")
    
    # Salesforce object names: letters, numbers, underscores
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]*$'
    if not re.match(pattern, sobject_name):
        raise ValueError(
            f"Invalid Salesforce object name: '{sobject_name}'. "
            f"Object names must start with a letter and contain only letters, numbers, and underscores."
        )
    
    return sobject_name


def validate_soql_filter(query_filter: str) -> None:
    """
    Validate SOQL WHERE clause filter for security issues.
    
    This function checks for common SQL/SOQL injection patterns and dangerous keywords.
    It should be called before using user-provided filters in SOQL queries.
    
    Args:
        query_filter: SOQL WHERE clause filter to validate
    
    Raises:
        ValueError: If filter contains dangerous patterns or keywords
    
    Example:
        >>> validate_soql_filter("Status = 'Active'")  # OK
        >>> validate_soql_filter("Status = 'Active'; DROP TABLE")  # Raises ValueError
    """
    if not query_filter:
        return
    
    # Check for dangerous patterns
    dangerous_patterns = [
        r';\s*DROP',
        r';\s*DELETE',
        r';\s*INSERT',
        r';\s*UPDATE',
        r';\s*TRUNCATE',
        r';\s*ALTER',
        r';\s*CREATE',
        r'--',  # SQL comments
        r'/\*',  # Multi-line comments
    ]
    
    filter_upper = query_filter.upper()
    
    for pattern in dangerous_patterns:
        if re.search(pattern, filter_upper, re.IGNORECASE):
            raise ValueError(
                f"Query filter contains potentially dangerous pattern: {pattern}. "
                f"Filter: {query_filter}"
            )
    
    # Check for dangerous standalone keywords
    dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'TRUNCATE', 'ALTER', 'CREATE', 'EXEC']
    
    # Split by common delimiters and check each token
    tokens = re.split(r'[\s,();]+', filter_upper)
    for token in tokens:
        if token in dangerous_keywords:
            raise ValueError(
                f"Query filter contains disallowed keyword: {token}. "
                f"Filter: {query_filter}"
            )


def _format_soql_value(value: Any, field_type: str = "auto") -> str:
    """
    Safely format a value for use in SOQL queries.
    
    IMPORTANT: SOQL datetime literals are NOT quoted and use ISO 8601 format.
    Strings ARE quoted and single quotes must be escaped.
    
    Args:
        value: Value to format
        field_type: Type hint for formatting ("datetime", "date", "string", "number", "auto")
    
    Returns:
        Properly formatted and escaped SOQL value
    
    References:
        https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_dateformats.htm
    """
    if value is None:
        return "null"
    
    # Auto-detect type if not specified
    if field_type == "auto":
        if isinstance(value, datetime):
            field_type = "datetime"
        elif isinstance(value, date):
            field_type = "date"
        elif isinstance(value, (int, float)):
            field_type = "number"
        elif isinstance(value, bool):
            field_type = "boolean"
        else:
            # Check if string looks like a datetime
            if isinstance(value, str):
                # Common datetime patterns from Salesforce
                if 'T' in value and ('Z' in value or '+' in value or value.count(':') >= 2):
                    field_type = "datetime"
                elif re.match(r'^\d{4}-\d{2}-\d{2}$', value):
                    field_type = "date"
                else:
                    field_type = "string"
            else:
                field_type = "string"
    
    # Format based on type
    if field_type == "datetime":
        if isinstance(value, str):
            # Already a string - validate ISO format and return unquoted
            if not re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', value):
                raise ValueError(f"Invalid datetime format: {value}. Expected ISO 8601 format.")
            # Ensure it ends with Z if no timezone specified
            if not (value.endswith('Z') or '+' in value or value.count('-') > 2):
                value = value + 'Z'
            return value  # NO QUOTES for datetime literals in SOQL
        elif isinstance(value, datetime):
            return value.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        else:
            raise ValueError(f"Cannot format {type(value).__name__} as datetime")
    
    elif field_type == "date":
        if isinstance(value, str):
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
                raise ValueError(f"Invalid date format: {value}. Expected YYYY-MM-DD.")
            return value  # NO QUOTES for date literals in SOQL
        elif isinstance(value, (datetime, date)):
            return value.strftime("%Y-%m-%d")
        else:
            raise ValueError(f"Cannot format {type(value).__name__} as date")
    
    elif field_type == "number":
        return str(value)
    
    elif field_type == "boolean":
        return "true" if value else "false"
    
    else:  # string or default
        value_str = str(value)
        # Escape single quotes by doubling them (SOQL standard)
        escaped = value_str.replace("'", "\\'")
        return f"'{escaped}'"


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
    source_sobject = _sanitize_sobject_name(source_sobject)
    
    # Validate and sanitize all field names
    if not fields:
        raise ValueError("Fields dictionary cannot be empty")
    
    source_fields = [_sanitize_field_name(field) for field in fields.keys()]
    
    # Build WHERE clause
    predicates = []
    
    # Validate and add filter if present
    if source_query_filter:
        validate_soql_filter(source_query_filter)
        predicates.append(f"({source_query_filter})")
    
    # Build incremental predicate with proper escaping
    if source_replication_key and last_state is not None:
        # Validate replication key
        source_replication_key = _sanitize_field_name(source_replication_key)
        
        # Format the value - assume datetime for replication keys
        formatted_value = _format_soql_value(last_state, field_type="datetime")
        predicates.append(f"{source_replication_key} > {formatted_value}")
    
    # Construct WHERE clause
    where_clause = ""
    if predicates:
        where_clause = f" WHERE {' AND '.join(predicates)}"
    
    # Build ORDER BY clause
    order_by_clause = ""
    if source_replication_key:
        order_by_clause = f" ORDER BY {_sanitize_field_name(source_replication_key)} ASC"
    
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
    # Only rename fields that exist in the dataframe
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
    
    Example:
        >>> fields = {"Id": "account_id", "Name": "account_name"}
        >>> for batch in fetch_data(sf, "Account", fields):
        ...     print(f"Got {len(batch)} records")
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
    
    # Log the query for debugging (can be removed in production)
    print(f"Executing SOQL: {soql_query}")
    
    # Execute bulk query
    try:
        # Get the bulk2 handler for the object
        bulk_handler = getattr(sf.bulk2, source_sobject)
        
        # Query and process chunks
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
        
        # Log completion
        if chunk_count == 0:
            print(f"No data returned for {source_sobject}")
        else:
            print(f"Successfully fetched {total_records} records from {source_sobject} in {chunk_count} chunks")
    
    except SalesforceMalformedRequest as e:
        # Provide more context for debugging
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