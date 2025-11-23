"""
Salesforce Bulk API v2 destination for DLT.

Supports insert, upsert, and replace operations using Salesforce Bulk API v2.
"""

from .destination import salesforce_bulk2

__all__ = ["salesforce_bulk2"]
__version__ = "0.1.0"