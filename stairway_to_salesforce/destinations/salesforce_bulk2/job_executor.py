"""
Salesforce Bulk API v2 job execution router.

This module acts as a dispatcher, routing DLT load packages to specific
operation services (insert, upsert, delete, replace).
"""

import logging
from typing import List, Optional, Union

from simple_salesforce import Salesforce

# Import the operation services from the operations package
from .operations import exec_delete, exec_insert, exec_replace, exec_upsert

# Initialize logger
logger = logging.getLogger(__name__)


def execute_job(
    sf_driver: Salesforce,
    target_name: str,
    salesforce_operation: str,
    primary_key: Optional[Union[str, List[str]]],
    file_path: str,
    key_resolver: Optional[object] = None,
) -> None:
    """
    Execute Salesforce Bulk API v2 job by dispatching to the appropriate service.

    Args:
        sf_driver: Authenticated Salesforce client.
        target_name: The SObject name (e.g., 'Account').
        salesforce_operation: The type of operation ('insert', 'upsert', 'delete', 'replace').
        primary_key: The field(s) used as identity (External IDs or 'Id').
        file_path: Path to the CSV data prepared by the data_processor.
        key_resolver: Component used to resolve External IDs to Salesforce IDs.
    """
    logger.debug("Dispatching %s operation for %s", salesforce_operation, target_name)

    # Mapping of operation strings to their service functions
    dispatch_map = {
        "insert": exec_insert,
        "upsert": exec_upsert,
        "delete": exec_delete,
        "replace": exec_replace,
    }

    # Verify that the requested operation is supported
    if salesforce_operation not in dispatch_map:
        raise ValueError(
            f"Unsupported operation '{salesforce_operation}' for table '{target_name}'. "
            f"Supported: {list(dispatch_map.keys())}"
        )

    # Execute the operation
    operation_func = dispatch_map[salesforce_operation]

    operation_func(
        sf_driver=sf_driver,
        target_name=target_name,
        file_path=file_path,
        primary_key=primary_key,
        key_resolver=key_resolver,
    )
    logger.debug("Successfully finished  %s on %s", salesforce_operation, target_name)
