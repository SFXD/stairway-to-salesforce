"""
Salesforce Bulk API v2 destination for DLT.

Supports insert, upsert, and replace operations using Salesforce Bulk API v2.
"""

from .salesforce_bulk2.destination_factory import get_sf_bulk2_destination


__version__ = "0.1.0"

__all__ = [
    "get_sf_bulk2_destination",
]
