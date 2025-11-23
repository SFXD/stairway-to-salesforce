"""DLT resource building and configuration validation for Salesforce sources."""

from typing import Any, Callable, Optional, Union
import dlt
from dlt.sources.helpers.requests import Session

from ...drivers.salesforce_driver import (
    SalesforceDriverAuth,
    resolve_salesforce_credentials,
    make_salesforce_driver,
)


def validate_resource_configs(configs: list[dict[str, Any]]) -> None:
    """
    Validate resource configurations for structure and required fields.
    
    Does NOT validate SOQL security - that's handled in query_builder.py
    
    Args:
        configs: List of resource configurations
    
    Raises:
        ValueError: If configs are missing required fields or have invalid structure
    """
    if not configs:
        raise ValueError("At least one resource configuration is required")
    
    required_fields = ["target_name", "target_primary_key", "source_sobject"]
    
    for i, config in enumerate(configs):
        # Check for required fields
        missing = [f for f in required_fields if not config.get(f)]
        if missing:
            raise ValueError(
                f"Config {i} missing required fields: {', '.join(missing)}"
            )
        
        # Validate structure
        if "fields" in config and not isinstance(config["fields"], dict):
            raise ValueError(f"Config {i}: 'fields' must be a dictionary")
        
        if "write_disposition" in config:
            valid_dispositions = ["append", "replace", "merge"]
            if config["write_disposition"] not in valid_dispositions:
                raise ValueError(
                    f"Config {i}: 'write_disposition' must be one of {valid_dispositions}"
                )
        
        # Validate that replication key exists in fields if both are provided
        if config.get("source_replication_key") and config.get("fields"):
            replication_key = config["source_replication_key"]
            if replication_key not in config["fields"]:
                raise ValueError(
                    f"Config {i}: source_replication_key '{replication_key}' "
                    f"must exist in fields dictionary"
                )


def build_resource(
    config: dict[str, Any],
    fetch_data_fn: Callable,
    credentials: Union[SalesforceDriverAuth, dict, str],
    session: Optional[Session]
):
    """
    Build a DLT resource from configuration.
    
    This function creates a DLT resource that will fetch data from Salesforce
    using the provided configuration and credentials.
    
    Args:
        config: Resource configuration dictionary
        fetch_data_fn: Function to fetch data from Salesforce (handles all SOQL security)
        credentials: Salesforce credentials (any supported format)
        session: Optional requests session
    
    Returns:
        Configured DLT resource function
    
    Example:
        >>> config = {
        ...     "target_name": "accounts",
        ...     "target_primary_key": "account_id",
        ...     "source_sobject": "Account",
        ...     "fields": {"Id": "account_id", "Name": "account_name"}
        ... }
        >>> resource = build_resource(config, fetch_data, credentials, None)
    """
    # Resolve credentials once at resource build time
    resolved_credentials = resolve_salesforce_credentials(credentials)
    
    # Extract config values
    target_name = config["target_name"]
    target_primary_key = config["target_primary_key"]
    source_sobject = config["source_sobject"]
    fields = config.get("fields", {})
    write_disposition = config.get("write_disposition", "append")
    source_replication_key = config.get("source_replication_key")
    source_query_filter = config.get("source_query_filter")
    target_column_types = config.get("target_column_types")
    
    # Setup incremental loading
    incremental_cursor = None
    replication_key_field = None
    
    if source_replication_key:
        replication_key_field = fields.get(source_replication_key, source_replication_key)
        incremental_cursor = dlt.sources.incremental(
            replication_key_field,
            initial_value=None
        )
    
    @dlt.resource(
        name=target_name,
        primary_key=target_primary_key,
        write_disposition=write_disposition,
        columns=target_column_types
    )
    def sf_resource(incremental_load=incremental_cursor):
        """
        Dynamically created Salesforce resource.
        Credentials are resolved and captured via closure.
        """
        # Create driver using resolved credentials
        try:
            driver = make_salesforce_driver(resolved_credentials, session)
        except Exception as e:
            raise RuntimeError(
                f"Failed to create Salesforce driver for {source_sobject}: {str(e)}"
            ) from e
        
        last_value = None
        if incremental_cursor and replication_key_field and incremental_load:
            last_value = incremental_load.last_value
        
        try:
            # fetch_data_fn handles ALL SOQL validation and security
            yield from fetch_data_fn(
                sf=driver,
                source_sobject=source_sobject,
                fields=fields,
                source_replication_key=source_replication_key,
                last_state=last_value,
                source_query_filter=source_query_filter
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to fetch data from {source_sobject}: {str(e)}"
            ) from e
    
    return sf_resource