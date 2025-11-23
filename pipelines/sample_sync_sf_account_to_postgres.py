#!/usr/bin/env python3
"""Pipeline to load Salesforce data."""
import dlt
from dlt_salesforce_advanced.sources.salesforce_bulk2 import salesforce_bulk2_source


def execute(environment: str = "dev") -> None:
    """Pipeline Example From Salesforce To PostgreSQL"""
    
    pipeline_name = "pipeline_source_salesforce_bulk2"
    source_system_key = "salesforce"
    target_system_key = "postgres"
    target_schema = "public"
    
    # Define resource configurations
    resource_configs = [
        {
            "target_name": "tb_accounts",
            "target_primary_key": "account_id",
            "source_sobject": "Account",
            "write_disposition": "merge",
            # Field mapping: "Source Field" : "Target Field"
            "fields": {
                "Id": "account_id",
                "Name": "account_name",
                "LastModifiedDate": "sf_modification_date",
                "Description": "Description",
                "CreatedDate": "CreatedDate",
                "CurrencyIsoCode": "CurrencyIsoCode",
                "Website": "Website",
                "Owner.Name": "sf_owner"
            },
            # Source replication key must exist in fields as key
            "source_replication_key": "LastModifiedDate",
            # Target column types - to fix field type for special fields (like URL)
            "target_column_types": {
                "website": {"data_type": "text"}
            },
            # Source query filter added to SOQL WHERE clause before timestamp selection
            "source_query_filter": None
        }
    ]
    
    # Load credentials based on environment
    source_credentials = dlt.secrets[f"{source_system_key}.{environment}"]
    target_credentials = dlt.secrets[f"{target_system_key}.{environment}"]

    # Create and run pipeline
    pipeline = dlt.pipeline(
        pipeline_name=pipeline_name,
        destination=dlt.destinations.postgres(credentials=target_credentials),
        dataset_name=target_schema,
        import_schema_path=".dlt/schemas/import",
        export_schema_path=".dlt/schemas/export"
    )
    
    # Run the source with configurations
    load_info = pipeline.run(salesforce_bulk2_source(resource_configs, credentials=source_credentials))
    print(load_info)


if __name__ == "__main__":
    import sys
    # Get environment from command line argument if provided
    environment = sys.argv[1] if len(sys.argv) > 1 else "dev"
    execute(environment)