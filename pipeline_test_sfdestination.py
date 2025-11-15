    
#!/usr/bin/env python3
"""Pipeline to load Salesforce data."""
import dlt
from typing import Iterator, Dict, Any
from stairway_to_salesforce.destinations.salesforce_bulk2.salesforce_bulk2 import salesforce_bulk2

@dlt.resource(
    name="StairwayToSalesforce__c",  # Salesforce object name
    write_disposition="append",  # or "replace", "merge"
    primary_key="Name",  # Important for merge/upsert operations 
    columns={
        "RecordLastModifiedDate__c": {"data_type": "text"}
    }
)
def salesforce_accounts() -> Iterator[Dict[str, Any]]:
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

def execute() -> None:    
    """run the pipeline"""        
    pipeline = dlt.pipeline(    pipeline_name= "pipeline_test_sfdestination2" , destination=salesforce_bulk2, 
                                import_schema_path=".dlt/schemas/import", export_schema_path=".dlt/schemas/export")    
    
    load_info = pipeline.run([salesforce_accounts()])  # schema_contract="freeze"
    print(load_info)

if __name__ == "__main__":
    execute()