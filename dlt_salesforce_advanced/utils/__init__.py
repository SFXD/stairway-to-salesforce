"""
Shared utilities for Salesforce operations.

This package contains common utilities used across Salesforce sources and destinations.
"""

from .salesforce_validators import (
    sanitize_sobject_name,
    sanitize_field_name,
    validate_soql_filter,
    format_soql_value,
)
from .logger_config import (
    get_rejected_records_path,
)
from .salesforce_api_helper import (
    process_csv_result
)

__all__ = [
    "sanitize_sobject_name",
    "sanitize_field_name",
    "validate_soql_filter",
    "format_soql_value",
    "get_rejected_records_path",
    "process_csv_result"
]