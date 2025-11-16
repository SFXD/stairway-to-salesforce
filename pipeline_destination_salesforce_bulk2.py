    
#!/usr/bin/env python3
"""Pipeline to load Salesforce data."""
import dlt
from typing import Iterator, Dict, Any
from stairway_to_salesforce.destinations.salesforce_bulk2 import salesforce_bulk2

@dlt.resource(
    name="StairwayToSalesforce__c",  # Salesforce object name
    write_disposition="append",  # or "replace", "merge"
    primary_key="Name",  # Important for merge/upsert operations 
    columns={
        "RecordLastModifiedDate__c": {"data_type": "text"}
    }
)
def mock_accounts() -> Iterator[Dict[str, Any]]:
    """
    Simple source with hardcoded Salesforce Account records
    """
    accounts = [
        {
            "Name": "DLT Account 1",
            "OwnerId": "00524000001QUIY",  # Replace with valid Salesforce User ID
            "RecordLastModifiedDate__c": "2025-11-15T00:00:00Z",
        },
        {
            "Name": "DLT Account 2",
            "OwnerId": "00524000001QUIY",
            "RecordLastModifiedDate__c": "2025-11-15T00:00:00Z",
        },
        {
            "Name": "DLT Account 3",
            "OwnerId": "00524000001QUIY",
            "RecordLastModifiedDate__c": "2025-11-15T00:00:00Z",
        },
    ]
    
    yield from accounts

def execute(environment: str = "dev") -> None:  

    #source_system_key = "mock"
    target_system_key = "salesforce"

    # Load credentials based on environment
    #source_credentials = dlt.secrets[f"{source_system_key}.{environment}"]
    target_credentials = dlt.secrets[f"{target_system_key}.{environment}"]

    """run the pipeline"""        
    pipeline = dlt.pipeline(    pipeline_name= "pipeline_destination_salesforce_bulk2" , destination=salesforce_bulk2(credentials=target_credentials), 
                                import_schema_path=".dlt/schemas/import", export_schema_path=".dlt/schemas/export")    
    
    load_info = pipeline.run([mock_accounts()])  # schema_contract="freeze"
    print(load_info)

if __name__ == "__main__":
    import sys
    # Get environment from command line argument if provided
    environment = sys.argv[1] if len(sys.argv) > 1 else "dev"
    execute(environment)