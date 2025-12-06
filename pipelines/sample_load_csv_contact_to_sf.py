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
import logging
from typing import Iterator, Dict, Any

import dlt
from dlt.sources.filesystem import filesystem, read_csv

from dlt_salesforce_advanced.drivers.salesforce_driver.sfdriver import get_salesforce_driver
from dlt_salesforce_advanced.destinations import salesforce_bulk2
from dlt_salesforce_advanced.components import SalesforceKeyResolver
# Import logging utilities

PIPELINE_BASE_NAME = "sample_load_csv_contacts_to_salesforce"

class PipelineDefinition:
    def __init__(
        self,
        args
    ):
        ### init global
        self.env =args.env
        self.pipeline_name = f"{PIPELINE_BASE_NAME}_{self.env}"
        self.logger = logging.getLogger("dlt")

        ### Source init
        self.csv_file_path = args.csv_file

        ### Target init      
        self.sf_credential_path= f"salesforce.{self.env}"
    
    def _create_transformer(self):
        @dlt.transformer(
            name="sf_contacts",
            write_disposition="append",
            table_name="Contact",
        )
        def transform(
            records: Iterator[Dict[str, Any]],
            credentials: str
        ) -> Iterator[Dict[str, Any]]:
            """
            Transform contacts to send them to Salesforce with
                - column mapping
                - external key resolution ( example for AccountId lookup)    
            Args:
                contacts: Iterator of contact dictionaries
                credentials: Salesforce credentials 
                
            Yields:
                contacts ready to be imported into Salesforce
            """
            ### Step 1: Safety step to have a list
            records_list = list(records)  

            ### Step 2: Check CSV Columns (on the first record)
            required_columns = ["Customer_Id", "First_Name", "Last_Name", "Email"]
            missing = [col for col in required_columns if col not in records_list[0]]
            if missing:
                raise ValueError(f"Missing required columns in record: {missing}")

            ### Step 3: Preparing the resolution of CustomerId as AccountId (with the external id field Customer_ID__c )
            resolver = SalesforceKeyResolver(credentials=credentials)
            account_sobject = "Account"
            account_key_field = "Customer_ID__c"
            # Extract all account key values from this dataset ( and deduplicate )
            account_key_values = {str(record["Customer_Id"]) for record in records_list if "Customer_Id" in record and record["Customer_Id"]}
            resolver.set_definition(sobject=account_sobject, key_field=account_key_field, key_values=account_key_values)

            ### Step 4: Build sf_contact records
            for record in records_list:
                # Map fields
                yield { 
                    "FirstName": record["First_Name"],
                    "LastName": record["Last_Name"],
                    "Email": record["Email"],
                    "AccountId" : resolver.try_resolve(account_sobject, account_key_field, record["Customer_Id"])
                }

        # End of create_transformer
        # return the newly created @dlt.transform    
        return transform

    def execute(
        self,
    ) -> None:        

        ### Step 1: Source
        source = filesystem(
            bucket_url=self.csv_file_path.rsplit('/', 1)[0],  # folder path
            file_glob=self.csv_file_path.rsplit('/', 1)[1]   # filename
        ) | read_csv()

        ### Step 2:  Transform
        transformer = self._create_transformer().bind(credentials=self.sf_credential_path)

        ### Step 3  Destination
        destination = salesforce_bulk2(credentials=f"{self.sf_credential_path}")

        ### Step 4:  Build the pipeline
        pipeline = dlt.pipeline(
            pipeline_name=f"{self.pipeline_name}",
            destination=destination,
            dataset_name="contacts"
        )
        
        ### Step 5 : run pipeline
        load_info = pipeline.run(source | transformer)

        ### Step 6 : post process
        print(f"  {load_info}")


if __name__ == "__main__":
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
        PipelineDefinition(args).execute()
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)