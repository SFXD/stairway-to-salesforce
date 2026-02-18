"""Main Salesforce Bulk API v2 source implementation."""

from typing import Any, Optional
import dlt
from dlt.sources.helpers.requests import Session

from .resource_builder import build_resource, validate_resource_configs
from .query_builder import fetch_data


def salesforce_bulk2_source(
    resource_configs: list[dict[str, Any]],
    credentials: str = "",
    session: Optional[Session] = None,
):
    """
    Dynamic Salesforce Bulk API v2 source.
    
    Args:
        resource_configs: List of resource configurations
        credentials: Salesforce credentials in any supported format:
            - SalesforceDriverAuth instance
            - dict with credential fields
            - str path to DLT secrets (e.g., "salesforce.production")
        session: Optional requests session
    
    Returns:
        DLT source with dynamically created resources
    """
    if credentials is None:
        raise ValueError(
            "Salesforce credentials must be provided. "
            "Either pass them explicitly or configure them in .dlt/secrets.toml"
        )
    
    validate_resource_configs(resource_configs)
    
    @dlt.source(name="salesforce_bulk2")
    def _source():
        """Inner source function that yields resources."""
        for config in resource_configs:
            yield build_resource(config, fetch_data, credentials, session)
    
    return _source()