"""
Salesforce Bulk API v2 destination for DLT.

This destination provides dynamic, configuration-driven access to Salesforce data
using the Bulk API v2 for efficient large-scale data ingestion.
"""

from .destination import salesforce_bulk2

__all__ = ["salesforce_bulk2"]

# Optional: expose version
__version__ = "0.1.0"