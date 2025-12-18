"""
Salesforce Bulk API v2 destination for DLT.

Refactored to use a Service/Action pattern with a centralized configuration 
layer for cleaner metadata validation.
"""

import dlt
import logging

from dlt.common.typing import TDataItems
from dlt.common.schema import TTableSchema

from dlt_salesforce_advanced.drivers.salesforce_driver.sfdriver import get_salesforce_driver
from dlt_salesforce_advanced.components import SalesforceKeyResolver
from .destination_config import SalesforceDestinationConfig
from .data_processor import prepare_data, cleanup_temp_file
from .job_executor import execute_job

logger = logging.getLogger("dlt")

@dlt.destination(
    name="salesforce_bulk2",
    loader_file_format="parquet",
    batch_size=10000,
    naming_convention="direct",
)
def salesforce_bulk2(
    items: TDataItems,
    table: TTableSchema,
    credentials: str = ""
) -> None:
    """
    DLT destination for Salesforce Bulk API v2 using Service/Action pattern.
    """
    # 1. Configuration & Validation Layer
    # This replaces the messy inline validation blocks
    config = SalesforceDestinationConfig.from_table_schema(table)
    
    # 2. Component Initialization
    try:
        driver = get_salesforce_driver(credentials)
        key_resolver = SalesforceKeyResolver(credentials=credentials)
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Salesforce components: {str(e)}") from e    
    
    # 3. Preparation and Execution
    file_path = None
    try:
        # Convert items to Bulk 2.0 compatible CSV
        file_path = prepare_data(items)
        
        # Dispatch to the Job Executor router
        execute_job(
            sf_driver=driver,
            target_name=config.target_object_name,
            salesforce_operation=config.salesforce_operation,
            primary_key=config.primary_key_field,
            file_path=file_path,
            key_resolver=key_resolver
        )
        
    finally:
        # Ensure cleanup of temporary CSV files
        if file_path:
            cleanup_temp_file(file_path)