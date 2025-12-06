"""
SOQL query building and data fetching for Salesforce Bulk API v2.

This module handles all SOQL query construction, validation, security checks,
and data fetching from Salesforce using the Bulk API v2.
"""

from typing import Optional, Iterable, Any
from simple_salesforce.exceptions import SalesforceMalformedRequest
from simple_salesforce import Salesforce
from dlt.common.typing import TDataItem
import logging
import io
import pandas as pd

# Import shared validators
from dlt_salesforce_advanced.utils.salesforce_validators import (
    sanitize_sobject_name,
    sanitize_field_name,
    validate_soql_filter,
    format_soql_value,
)


# Initialize logger
logger = logging.getLogger("dlt")


def _build_soql_query(
    source_sobject: str,
    fields: dict[str, str],
    source_query_filter: Optional[str] = None,
    source_replication_key: Optional[str] = None,
    last_state: Optional[Any] = None
) -> str:
    """
    Build a secure SOQL query with proper validation and escaping.
    """
    logger.debug(f"Building SOQL query for {source_sobject}")
    
    # Validate and sanitize object name
    source_sobject = sanitize_sobject_name(source_sobject)
    
    # Validate and sanitize all field names (allow relationship notation)
    if not fields:
        raise ValueError("Fields dictionary cannot be empty")
    
    source_fields = [sanitize_field_name(field) for field in fields.keys()]
    logger.debug(f"Selected fields: {', '.join(source_fields[:5])}..." if len(source_fields) > 5 else f"Selected fields: {', '.join(source_fields)}")
    
    # Build WHERE clause
    predicates = []
    
    # Validate and add filter if present
    if source_query_filter:
        validate_soql_filter(source_query_filter)
        predicates.append(f"({source_query_filter})")
        logger.debug(f"Applied filter: {source_query_filter}")
    
    # Build incremental predicate with proper escaping
    if source_replication_key and last_state is not None:
        # Validate replication key
        source_replication_key = sanitize_field_name(source_replication_key)
        
        # Format the value - assume datetime for replication keys
        formatted_value = format_soql_value(last_state, field_type="datetime")
        predicates.append(f"{source_replication_key} > {formatted_value}")
        logger.info(f"Incremental load: {source_replication_key} > {formatted_value}")
    
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
    
    logger.debug(f"Generated SOQL: {query}")
    return query


def _process_result(chunk: Any, fields: dict[str, str]) -> Iterable[TDataItem]:
    """
    Process a chunk of results from Salesforce Bulk API.
    """
    # Handle different chunk types from Bulk API
    if isinstance(chunk, str):
        # CSV string response
        try:
            df = pd.read_csv(io.StringIO(chunk))
            logger.debug(f"Parsed CSV chunk with {len(df)} rows")
        except Exception as e:
            logger.error(f"Failed to parse CSV chunk: {str(e)}")
            raise ValueError(f"Failed to parse CSV chunk: {str(e)}") from e
    
    elif isinstance(chunk, list):
        # List of dictionaries response
        if not chunk:
            return []
        df = pd.DataFrame(chunk)
        logger.debug(f"Converted list chunk with {len(df)} rows")
    
    else:
        logger.error(f"Unexpected chunk type: {type(chunk).__name__}")
        raise ValueError(
            f"Unexpected chunk type: {type(chunk).__name__}. "
            f"Expected str (CSV) or list (records)"
        )
    
    # Handle empty results
    if df.empty:
        logger.debug("Chunk is empty, skipping")
        return []
    
    # Rename columns based on field mapping
    rename_map = {
        source: target
        for source, target in fields.items()
        if source in df.columns
    }
    
    if rename_map:
        df.rename(columns=rename_map, inplace=True)
        logger.debug(f"Renamed {len(rename_map)} columns")
    
    # Convert to list of dictionaries
    records = df.to_dict(orient="records")
    logger.debug(f"Processed {len(records)} records from chunk")
    return records


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
    """
    logger.info(f"Starting data fetch from {source_sobject}")
    
    # Validate inputs
    if not sf:
        logger.error("Salesforce client is None")
        raise ValueError("Salesforce client cannot be None")
    
    if not fields:
        logger.error("Fields mapping is empty")
        raise ValueError("Fields mapping cannot be empty")
    
    logger.info(f"Fetching {len(fields)} field(s) from {source_sobject}")
    
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
        logger.error(f"Failed to build SOQL query: {str(e)}")
        raise ValueError(f"Failed to build SOQL query: {str(e)}") from e
    
    logger.info(f"Executing SOQL: {soql_query}")
    
    # Execute bulk query
    try:
        bulk_handler = getattr(sf.bulk2, source_sobject)
        
        chunk_count = 0
        total_records = 0
        
        for chunk in bulk_handler.query(soql_query):
            chunk_count += 1
            logger.debug(f"Processing chunk {chunk_count}")
            
            try:
                records = _process_result(chunk, fields)
            except Exception as e:
                logger.error(f"Failed to process chunk {chunk_count}: {str(e)}")
                raise RuntimeError(
                    f"Failed to process chunk {chunk_count} for {source_sobject}: {str(e)}"
                ) from e
            
            if records:
                record_count = len(records)
                total_records += record_count
                logger.debug(f"Yielding {record_count} records from chunk {chunk_count}")
                yield records
        
        if chunk_count == 0:
            logger.warning(f"No data returned for {source_sobject}")
        else:
            logger.info(
                f"Successfully fetched {total_records} record(s) from {source_sobject} "
                f"in {chunk_count} chunk(s)"
            )
    
    except SalesforceMalformedRequest as e:
        logger.error(f"Malformed SOQL query for {source_sobject}: {str(e)}")
        raise SalesforceMalformedRequest(
            f"Malformed SOQL query for {source_sobject}. "
            f"Query: {soql_query}. "
            f"Error: {str(e)}"
        ) from e
    
    except AttributeError as e:
        logger.error(f"Invalid Salesforce object: {source_sobject}")
        raise ValueError(
            f"Invalid Salesforce object: '{source_sobject}'. "
            f"Ensure the object exists and you have permission to access it."
        ) from e
    
    except Exception as e:
        logger.error(f"Failed to fetch data from {source_sobject}: {str(e)}")
        raise RuntimeError(
            f"Failed to fetch data from {source_sobject}: {str(e)}"
        ) from e