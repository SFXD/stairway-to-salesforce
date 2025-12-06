"""
Salesforce Bulk API v2 destination for DLT.

Supports insert (append), upsert (merge), and replace write dispositions.
"""

import dlt
from dlt.common.typing import TDataItems
from dlt.common.schema import TTableSchema
from simple_salesforce import Salesforce

from dlt_salesforce_advanced.drivers.salesforce_driver import (
    SalesforceDriverAuth,
    resolve_salesforce_credentials,
)
from .data_processor import prepare_data, cleanup_temp_file
from .job_executor import execute_job


@dlt.destination(
    name="salesforce_bulk2",
    loader_file_format="parquet",
    batch_size=10000,
    naming_convention="direct"
)
def salesforce_bulk2(
    items: TDataItems,
    table: TTableSchema,
    credentials: SalesforceDriverAuth = dlt.secrets.value,
    sf_driver: Salesforce = None
) -> None:
    """
    DLT destination for Salesforce Bulk API v2.
    
    Supports three write dispositions:
    - append: Insert new records
    - merge: Upsert records using external ID field
    - replace: Delete all existing records, then insert new ones
    
    Args:
        items: Data items to load (file path, RecordBatch, or iterable)
        table: Table schema with metadata including write_disposition
        credentials: Salesforce authentication credentials
        sf_driver: simple-salesforce driver
    
    Raises:
        ValueError: If required metadata is missing or invalid
        RuntimeError: If Salesforce API operations fail
    
    Example:
        >>> @dlt.resource(
        ...     name="Account",
        ...     write_disposition="merge",
        ...     primary_key="Id"
        ... )
        >>> def accounts():
        ...     yield [{"Id": "001...", "Name": "Acme Corp"}]
    """
    # Validate required table metadata
    write_disposition = table.get("write_disposition")
    if not write_disposition:
        raise ValueError(
            f"write_disposition must be specified for table '{table.get('name', 'unknown')}'. "
            f"Valid values: 'append', 'merge', 'replace'"
        )
    
    target_name = table.get("name")
    if not target_name:
        raise ValueError("Table name must be specified for Salesforce destination")
    
    # Validate write_disposition value
    valid_dispositions = ["append", "merge", "replace"]
    if write_disposition not in valid_dispositions:
        raise ValueError(
            f"Invalid write_disposition '{write_disposition}' for table '{target_name}'. "
            f"Must be one of: {', '.join(valid_dispositions)}"
        )
    
    # Validate primary_key for merge operations
    primary_key = table.get("primary_key")
    if write_disposition == "merge" and not primary_key:
        raise ValueError(
            f"Primary key must be specified for merge operations on '{target_name}'"
        )

    if sf_driver is None:
        # Initialize Salesforce driver
        resolved_credentials = resolve_salesforce_credentials(credentials)
        try:
            driver = make_salesforce_driver(resolved_credentials)
        except Exception as e:
            logger.error(f"Failed to initialize Salesforce driver: {str(e)}")
            raise RuntimeError(
                f"Failed to initialize Salesforce driver: {str(e)}"
            ) from e    
    
    # Prepare data file
    file_path = None
    try:
        # Convert items to CSV file
        file_path = prepare_data(items)
        
        # Execute Bulk API job with appropriate disposition
        execute_job(
            credentials=resolved_credentials,
            target_name=target_name,
            write_disposition=write_disposition,
            primary_key=primary_key,
            file_path=file_path
        )
        
    finally:
        # Always attempt cleanup
        if file_path:
            cleanup_temp_file(file_path)