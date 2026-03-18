"""
Salesforce lookup resolver for DLT pipelines.

This module provides utilities for mapping external keys to Salesforce IDs,
with support for efficient caching and both REST and Bulk API queries.
"""

from .base_pipeline.base_pipeline import BasePipeline
from .salesforce_key_resolver.resolver import SalesforceKeyResolver
from .salesforce_key_resolver.resolver_factory import get_salesforce_key_resolver


__version__ = "1.0.0"

__all__ = [
    "SalesforceKeyResolver",
    "get_salesforce_key_resolver",
    "BasePipeline",
]
