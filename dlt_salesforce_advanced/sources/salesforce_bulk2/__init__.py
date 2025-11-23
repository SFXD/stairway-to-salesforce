"""
Salesforce Bulk API v2 source for DLT.

This source provides dynamic, configuration-driven access to Salesforce data
using the Bulk API v2 for efficient large-scale data extraction.
"""

from .source import salesforce_bulk2_source

__all__ = ["salesforce_bulk2_source"]

# Optional: expose version
__version__ = "0.1.0"