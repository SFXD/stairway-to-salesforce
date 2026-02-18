"""DLT resource building and configuration validation for Salesforce sources."""

from typing import Any, Callable, Optional
import dlt
from dlt.sources.helpers.requests import Session

from ...drivers.salesforce_driver.sfdriver import get_salesforce_driver


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
    
    required_fields = ["name", "primary_key", "sobject"]    
    for i, config in enumerate(configs):
        # Check for required fields
        missing = [f for f in required_fields if not config.get(f)]
        if missing:
            raise ValueError(
                f"Config {i} missing required fields: {', '.join(missing)}"
            )
        
        # Validate structure
        if "fields" in config and not isinstance(config["fields"], list):
            raise ValueError(f"Config {i}: 'fields' must be a list")        
        if "write_disposition" in config:
            valid_dispositions = ["append", "replace", "merge"]
            if config["write_disposition"] not in valid_dispositions:
                raise ValueError(
                    f"Config {i}: 'write_disposition' must be one of {valid_dispositions}"
                )
        
        # Validate that replication key exists in fields if both are provided
        if config.get("replication_key") and config.get("fields"):
            replication_key = config["replication_key"]
            if replication_key not in config["fields"]:
                raise ValueError(
                    f"Config {i}: replication_key '{replication_key}' "
                    f"must exist in fields list"
                )

def build_resource(
    config: dict[str, Any],
    fetch_data_fn: Callable,
    credentials: str, 
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
        ...     "name": "accounts",
        ...     "primary_key": "account_id",
        ...     "sobject": "Account",
        ...     "fields": {"Id", "Name",...}
        ... }
        >>> resource = build_resource(config, fetch_data, credentials, None)
    """
    # Extract config values
    name = config["name"]
    primary_key = config["primary_key"]
    sobject = config["sobject"]
    fields = config.get("fields", [])
    write_disposition = config.get("write_disposition", "append")
    replication_key = config.get("replication_key")
    query_filter = config.get("query_filter")
    column_types = config.get("column_types")
    
    # Setup incremental loading
    incremental_cursor = None    
    if replication_key:
        incremental_cursor = dlt.sources.incremental(
            replication_key,
            initial_value=None
        )
    
    @dlt.resource(
        name=name,
        primary_key=primary_key,
        write_disposition=write_disposition,
        columns=column_types
    )
    def sf_resource(incremental_load=incremental_cursor):
        """
        Dynamically created Salesforce resource.
        Credentials are resolved and captured via closure.
        """
        # Create driver using resolved credentials
        try:
            driver = get_salesforce_driver(credentials, session)
        except Exception as e:
            raise RuntimeError(
                f"Failed to create Salesforce driver for {sobject}: {str(e)}"
            ) from e
        
        last_value = None
        if incremental_cursor and replication_key and incremental_load:
            last_value = incremental_load.last_value
        
        try:
            # fetch_data_fn handles ALL SOQL validation and security            
            for chunk in fetch_data_fn(
                sf=driver,
                sobject=sobject,
                fields=fields,
                replication_key=replication_key,
                last_state=last_value,
                query_filter=query_filter
            ):
                print("resource.chunk=",chunk)
                yield chunk            
        except Exception as e:
            raise RuntimeError(
                f"Failed to fetch data from {sobject}: {str(e)}"
            ) from e
    
    return sf_resource