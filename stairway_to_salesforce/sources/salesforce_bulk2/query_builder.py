"""
SOQL query building and data fetching for Salesforce Bulk API v2.

This module handles all SOQL query construction, validation, security checks,
and data fetching from Salesforce using the Bulk API v2.
"""

import io
import logging
from typing import Any, Iterable, Optional

import pandas as pd
from dlt.common.typing import TDataItem
from simple_salesforce import Salesforce
from simple_salesforce.exceptions import SalesforceMalformedRequest

from stairway_to_salesforce.utils.salesforce_validators import (
    format_soql_value,
    sanitize_field_name,
    sanitize_sobject_name,
    validate_soql_filter,
)

logger = logging.getLogger(__name__)


def _build_soql_query(
    sobject: str,
    fields: list[str],
    query_filter: Optional[str] = None,
    replication_key: Optional[str] = None,
    last_state: Optional[Any] = None,
) -> str:
    """
    Build a secure SOQL query with proper validation and escaping.
    """
    logger.debug(f"Building SOQL query for {sobject}")

    # Build SELECT/FROM Clause
    sobject = sanitize_sobject_name(sobject)
    if not fields:
        raise ValueError("Fields list cannot be empty")

    source_fields = [sanitize_field_name(field) for field in fields]
    logger.debug(
        f"Selected fields: {', '.join(source_fields[:5])}..."
        if len(source_fields) > 5
        else f"Selected fields: {', '.join(source_fields)}"
    )

    # Build WHERE Clause
    predicates = []
    if query_filter:
        validate_soql_filter(query_filter)
        predicates.append(f"({query_filter})")
        logger.debug(f"Applied filter: {query_filter}")
    if replication_key and last_state is not None:
        replication_key = sanitize_field_name(replication_key)

        # Format the value - assume datetime for replication keys
        formatted_value = format_soql_value(last_state, field_type="datetime")
        predicates.append(f"{replication_key} > {formatted_value}")
        logger.info(f"Incremental load: {replication_key} > {formatted_value}")

    where_clause = ""
    if predicates:
        where_clause = f" WHERE {' AND '.join(predicates)}"

    # Build ORDER BY clause
    order_by_clause = ""
    if replication_key:
        order_by_clause = f" ORDER BY {sanitize_field_name(replication_key)} ASC"

    # Build final query
    query = (
        f"SELECT {', '.join(source_fields)} FROM {sobject}{where_clause}{order_by_clause} LIMIT 2"
    )
    logger.debug(f"Generated SOQL: {query}")
    return query


def _normalize_result(chunk: Any) -> Iterable[TDataItem]:
    """
    Process a chunk of results from Salesforce Bulk API.
    """
    # Handle different chunk types from Bulk API
    if isinstance(chunk, str):
        try:
            df = pd.read_csv(io.StringIO(chunk))
            logger.debug(f"Parsed CSV chunk with {len(df)} rows")
        except Exception as e:
            logger.error(f"Failed to parse CSV chunk: {str(e)}")
            raise ValueError(f"Failed to parse CSV chunk: {str(e)}") from e

    elif isinstance(chunk, list):
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

    # Prepare return values
    records = df.to_dict(orient="records")
    logger.debug(f"Processed {len(records)} records from chunk")
    return records


def _execute_bulk_query(sf, sobject, soql_query):
    bulk_handler = getattr(sf.bulk2, sobject)
    chunk_count = 0
    total_records = 0

    # For each Bulk2 API file result (=chunk)
    for chunk in bulk_handler.query(soql_query):
        chunk_count += 1
        logger.debug(f"Processing chunk {chunk_count}")

        # Normalize the result (to make sure the format is a dictionnary)
        try:
            records = _normalize_result(chunk)
        except Exception as e:
            logger.error(f"Failed to process chunk {chunk_count}: {str(e)}")
            raise RuntimeError(
                f"Failed to process chunk {chunk_count} for {sobject}: {str(e)}"
            ) from e

        # Return the group of records
        yield records

    if chunk_count == 0:
        logger.warning(f"No data returned for {sobject}")
    else:
        logger.info(
            f"Successfully fetched {total_records} record(s) from {sobject} "
            f"in {chunk_count} chunk(s)"
        )


def fetch_data(
    sf: Salesforce,
    sobject: str,
    fields: list[str],
    replication_key: Optional[str] = None,
    last_state: Optional[Any] = None,
    query_filter: Optional[str] = None,
) -> Iterable[TDataItem]:
    """
    Fetch data from Salesforce using Bulk API v2.

    All SOQL query validation and security checks are performed here.
    """
    logger.info(f"Starting data fetch from {sobject}")

    # Validate inputs
    if not sf:
        logger.error("Salesforce client is None")
        raise ValueError("Salesforce client cannot be None")

    if not fields:
        logger.error("Fields mapping is empty")
        raise ValueError("Fields mapping cannot be empty")

    logger.info(f"Fetching {len(fields)} field(s) from {sobject}")

    # Build SOQL query
    try:
        soql_query = _build_soql_query(sobject, fields, query_filter, replication_key, last_state)
    except ValueError as e:
        logger.error(f"Failed to build SOQL query: {str(e)}")
        raise ValueError(f"Failed to build SOQL query: {str(e)}") from e

    logger.info(f"Executing SOQL: {soql_query}")

    # Execute bulk query
    try:
        yield from _execute_bulk_query(sf, sobject, soql_query)

    except SalesforceMalformedRequest as e:
        logger.error(f"Malformed SOQL query for {sobject}: {str(e)}")
        raise SalesforceMalformedRequest(
            f"Malformed SOQL query for {sobject}. " f"Query: {soql_query}. " f"Error: {str(e)}"
        ) from e

    except AttributeError as e:
        logger.error(f"Invalid Salesforce object: {sobject}")
        raise ValueError(
            f"Invalid Salesforce object: '{sobject}'. "
            f"Ensure the object exists and you have permission to access it."
        ) from e

    except Exception as e:
        logger.error(f"Failed to fetch data from {sobject}: {str(e)}")
        raise RuntimeError(f"Failed to fetch data from {sobject}: {str(e)}") from e
