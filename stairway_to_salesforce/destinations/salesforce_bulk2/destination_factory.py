"""
Salesforce Bulk API v2 destination for DLT.

Refactored to use a Service/Action pattern with a centralized configuration
layer for cleaner metadata validation.
"""

import logging

import dlt
from dlt.common.schema import TTableSchema
from dlt.common.typing import TDataItems

from stairway_to_salesforce.components import get_sf_key_resolver
from stairway_to_salesforce.drivers import get_sf_driver

from .data_processor import cleanup_temp_file, prepare_data
from .destination_config import SalesforceDestinationConfig
from .job_executor import execute_job


logger = logging.getLogger(__name__)


@dlt.destination(
    name="salesforce_bulk2",
    loader_file_format="parquet",
    batch_size=10000,
    naming_convention="direct",
)
def get_sf_bulk2_destination(items: TDataItems, table: TTableSchema, credentials: str = "") -> None:
    """
    DLT destination for Salesforce Bulk API v2 using Service/Action pattern.
    """
    # 1. Configuration & Validation Layer
    # This replaces the messy inline validation blocks
    config = SalesforceDestinationConfig.from_table_schema(table)

    # 2. Component Initialization
    driver = get_sf_driver(credentials)
    key_resolver = get_sf_key_resolver(credentials=credentials)

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
            key_resolver=key_resolver,
        )
    except Exception as e:
        logger.error(
            "Critical failure"
            f" during {config.salesforce_operation}"
            f" on {config.target_object_name}: {str(e)}"
        )

    finally:
        # Ensure cleanup of temporary CSV files
        if file_path:
            cleanup_temp_file(file_path)
