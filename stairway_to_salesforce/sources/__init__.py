"""
Salesforce Bulk API v2 source for DLT.

This source provides dynamic, configuration-driven access to Salesforce data
using the Bulk API v2 for efficient large-scale data extraction.
"""

from .salesforce_bulk2.source_factory import get_sf_bulk2_source


__version__ = "0.1.0"

__all__ = ["get_sf_bulk2_source"]
