"""
Salesforce Bulk API v2 destination for DLT.

Supports append and replace write dispositions with custom Salesforce operations.
Use the 'operation' hint to specify: insert, upsert, update, or delete.
"""

import dlt
from dlt.common.typing import TDataItems
from dlt.common.schema import TTableSchema

from dlt_salesforce_advanced.drivers.salesforce_driver.sfdriver import get_salesforce_driver
from .data_processor import prepare_data, cleanup_temp_file
from .job_executor import execute_job

@dlt.destination(
    name="salesforce_bulk2",
    loader_file_format="parquet",
    batch_size=10000,
    naming_convention="direct",
)
def salesforce_bulk2(
    items: TDataItems,
    table: TTableSchema,
    credentials: str =""
) -> None:
    """
    DLT destination for Salesforce Bulk API v2.
    
    Supports two write dispositions:
    - append: Load records with specified Salesforce operation
    - replace: Delete all existing records, then insert new ones
    
    For 'append' disposition, use the 'salesforce-operation' table hint (REQUIRED):
    - insert: Insert new records
    - upsert: Insert or update records based on external ID
    - delete: Delete records based on ID
    
    Example usage:
        @dlt.transformer(
            write_disposition="append",
            table_name="Contact",
            primary_key="Email",
            salesforce-operation="upsert"  # Custom hint
        )
    
    Args:
        items: Data items to load (file path, RecordBatch, or iterable)
        table: Table schema with metadata including write_disposition
        credentials: dlt secret path to credential
    
    Raises:
        ValueError: If required metadata is missing or invalid
        RuntimeError: If Salesforce API operations fail
    """
     
    # Validate write_disposition
    write_disposition = table.get("write_disposition")
    if not write_disposition:
        raise ValueError(
            f"write_disposition must be specified for table '{target_name}'. "
            f"Valid values: 'append', 'replace'"
        )    
    valid_dispositions = ["append", "replace"]
    if write_disposition not in valid_dispositions:
        raise ValueError(
            f"Invalid write_disposition '{write_disposition}' for table '{target_name}'. "
            f"Must be one of: {', '.join(valid_dispositions)}. "
            f"Note: 'merge' is not supported - use write_disposition='append' with "
            f"operation='upsert' instead."
        )

    # Validate sobject target name
    target_name = table.get("name")
    if not target_name:
        raise ValueError("Table name must be specified for Salesforce destination")
    
    # Extract primary key early for validation
    primary_key = table.get("primary_key")    
    # If top-level PK is missing, check columns
    if not primary_key and "columns" in table:
        primary_key = [
            col_name 
            for col_name, col_def in table["columns"].items() 
            if col_def.get("primary_key") is True
        ]
        
        if primary_key and len(primary_key) == 1:
            primary_key = primary_key[0]

    # Validate primary_key for merge operations
    if write_disposition == "merge" and not primary_key:
        raise ValueError(
            f"Primary key must be specified for merge operations on '{target_name}'"
        )

    # Validate x-salesforce-operation
    salesforce_operation = table.get("x-salesforce-operation")
    # Handle replace disposition with strict validation
    if write_disposition == "replace":
        # SECURITY: Replace should only be used when explicitly intended
        # Reject if primary_key or salesforce_operation are set
        if primary_key:
            raise ValueError(
                f"Replace write disposition for table '{target_name}' should not have a primary_key. "
                f"Remove the primary_key to confirm you intend to delete ALL records and insert new ones. "
                f"If you want conditional updates, use write_disposition='append' with operation='upsert'."
            )
        
        if salesforce_operation:
            raise ValueError(
                f"Replace write disposition for table '{target_name}' should not have salesforce_operation set. "
                f"Found: '{salesforce_operation}'. "
                f"Remove salesforce_operation to confirm you intend to delete ALL records and insert new ones. "
                f"If you want '{salesforce_operation}' operation, use write_disposition='append' instead."
            )
        
        # For replace, we always do delete + insert
        salesforce_operation = "replace"
        primary_key = None
    else:
        # salesforce_operation definitions
        valid_operations = ["insert", "upsert", "delete"]
        operations_with_key = ["update","delete"]

        # For append disposition, salesforce_operation is REQUIRED
        if not salesforce_operation:
            raise ValueError(
                f"operation must be specified for append write disposition on table '{target_name}'. "
                f"Valid values: {', '.join(valid_operations)}. "
                f"Example: Add operation='upsert' to your transformer hints."
            )
        
        if salesforce_operation not in valid_operations:
            raise ValueError(
                f"Invalid salesforce_operation '{salesforce_operation}' for table '{target_name}'. "
                f"Must be one of: {', '.join(valid_operations)}"
            )
        
        # Validate primary_key for operations that require it
        if salesforce_operation in operations_with_key and not primary_key:
            raise ValueError(
                f"Primary key must be specified for '{salesforce_operation}' operations on '{target_name}'. "
                f"The primary key is used as the external ID field for matching records."
            )            
    
    #check the credentials and create the sf driver if necessary (will be cached for further use)
    try:
        driver = get_salesforce_driver(credentials)
    except Exception as e:
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
            sf_driver=driver,
            target_name=target_name,
            salesforce_operation=salesforce_operation,
            primary_key=primary_key,
            file_path=file_path
        )
        
    finally:
        # Always attempt cleanup
        if file_path:
            cleanup_temp_file(file_path)