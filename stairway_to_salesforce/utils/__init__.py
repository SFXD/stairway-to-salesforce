# Copyright 2025-2026 Bertrand Leymarios, Geoffrey Bessereau
# and the Stairway to Salesforce Contributors
# Licensed under the Apache License, Version 2.0 (the "License")

"""
Shared utilities for Salesforce operations.

This package contains common utilities used across Salesforce sources and destinations.
"""

from .logger_config import get_rejected_records_path
from .salesforce_api_helper import process_csv_result
from .salesforce_validators import (
    format_soql_value,
    sanitize_field_name,
    sanitize_sobject_name,
    validate_soql_filter,
)


__all__ = [
    "sanitize_sobject_name",
    "sanitize_field_name",
    "validate_soql_filter",
    "format_soql_value",
    "get_rejected_records_path",
    "process_csv_result",
]
