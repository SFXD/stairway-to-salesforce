#!/usr/bin/env python3
"""
Optimized contact loading pipeline using DLT.

Clean, modular pipeline using:
- Custom csv_contacts_source for CSV loading
- SalesforceKeyResolver for ID mapping
- contact_enrichment transformer for data enrichment
"""
import argparse
import sys
from typing import Iterator, Dict, Any

import dlt
from dlt.sources.filesystem import filesystem, read_csv

from dlt_salesforce_advanced.destinations.salesforce_bulk2 import salesforce_bulk2
from dlt_salesforce_advanced.components.salesforce_key_resolver import get_salesforce_key_resolver
# Import logging utilities
from dlt_salesforce_advanced.utils.logger_config import get_salesforce_logger

# Initialize logger
logger = get_salesforce_logger('sample_load_csv_contact_to_sf', log_dir='.dlt/logs')

@dlt.transformer(
    name="sf_contacts",
    write_disposition="append",
    table_name="Contact",
)
def transform_sf_contacts(
    records: Iterator[Dict[str, Any]],
    credentials=dlt.secrets.value
) -> Iterator[Dict[str, Any]]:
    """
    Transform contacts to send them to Salesforce with
        - column mapping
        - external key resolution ( example for AccountId lookup)    
    Args:
        contacts: Iterator of contact dictionaries
        credentials: Salesforce credentials (default: dlt.secrets.value)
        
    Yields:
        contacts ready to be imported into Salesforce
    """
    # Step 1: Safety step to have a list
    records_list = list(records)  

    # Step 2: Check CSV Columns (on the first record)
    required_columns = ["Customer_Id", "First_Name", "Last_Name", "Email"]
    missing = [col for col in required_columns if col not in records_list[0]]
    if missing:
        raise ValueError(f"Missing required columns in record: {missing}")

    # Step 3: Preparing the resolution of CustomerId as AccountId (with the external id field Customer_ID__c )
    resolver = get_salesforce_key_resolver(credentials=credentials, logger=logger)
    account_sobject = "Account"
    account_key_field = "Customer_ID__c"
    # Extract all account key values from this dataset ( and deduplicate )
    account_key_values = {str(record["Customer_Id"]) for record in records_list if "Customer_Id" in record and record["Customer_Id"]}
    resolver.set_definition(sobject=account_sobject, key_field=account_key_field, key_values=account_key_values)
    # Step 4: Build sf_contact records
    for record in records_list:
        # Map fields
        yield { 
            "FirstName": record["First_Name"],
            "LastName": record["Last_Name"],
            "Email": record["Email"],
            "AccountId" : resolver.try_resolve(account_sobject, account_key_field, record["Customer_Id"])
        }

def execute(
    args
) -> None:
    # get arguments
    env= args.env
    csv_file_path = args.csv_file

    target_system_key = "salesforce"
    
    # Load Salesforce credentials
    target_credential = dlt.secrets[f"{target_system_key}.{env}"]
      
    # Build data pipeline: CSV → Enrichment → Destination
    #source = filesystem(file_glob=csv_file_path) | read_csv()    
    source = filesystem(
        bucket_url=csv_file_path.rsplit('/', 1)[0],  # folder path
        file_glob=csv_file_path.rsplit('/', 1)[1]   # filename
    ) | read_csv()

    transformer = transform_sf_contacts(credentials=target_credential)

    # Create DLT pipeline
    pipeline = dlt.pipeline(
        pipeline_name=f"load_csv_contacts_{env}",
        destination=salesforce_bulk2(credentials=target_credential),
        dataset_name="contacts"
    )
    
    load_info = pipeline.run(source | transformer)
    print(f"  {load_info}")


def main():
    parser = argparse.ArgumentParser(
        description="Stairway to Salesforce - specific pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--env',
        default='dev',
        help='Salesforce environment (default: dev)'
    )
    parser.add_argument(
        'csv_file',
        help='Path to CSV file with contacts'
    )
    args = parser.parse_args()
    
    try:
        execute(args)
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()