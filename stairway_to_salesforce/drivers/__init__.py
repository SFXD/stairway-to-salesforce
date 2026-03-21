"""
Salesforce lookup resolver for DLT pipelines.

This module provides utilities for mapping external keys to Salesforce IDs,
with support for efficient caching and both REST and Bulk API queries.
"""

from .salesforce_driver.driver_factory import get_sf_driver


__version__ = "1.0.0"

__all__ = [
    "get_sf_driver",
]
