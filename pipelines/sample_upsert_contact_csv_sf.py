#!/usr/bin/env python3
"""
Sample pipeline upserting contacts from a CSV file to Salesforce
- Using BasePipeline component, SalesforceKeyResolver Component and SalesforceBulk2 Destination with an upsert operation

Process:
- CSV File is loadded ( sample is data/upsert_contacts.csv )
- Contacts are transformed in the pipeline
    - keeping only specific columns (if additional columns are present in the csv)
    - resolving the Account Customer Id (=Custom External Id field for this sample)  as a Salesforce Id, using 
- Contacts are upserted to Salesforce based on the Email as External Id


"""
import logging
from typing import Iterator, Dict, Any

import dlt
from dlt.sources.filesystem import filesystem, read_csv

from dlt_salesforce_advanced.destinations import salesforce_bulk2
from dlt_salesforce_advanced.components import SalesforceKeyResolver
from dlt_salesforce_advanced.components import BasePipeline

class UpsertContactPipeline(BasePipeline):
    """
    Defines the specific logic for upserting contacts from CSV to Salesforce.
    """

    def execute(self) -> None:
        """
        Implementation of the DLT pipeline steps.
        """
        # Step 1: Initialize Source from CSV
        source_resource = filesystem(
            bucket_url=self.csv_file_path.rsplit('/', 1)[0],
            file_glob=self.csv_file_path.rsplit('/', 1)[1]
        ) | read_csv()

        # Step 2: Define Transformer directly
        @dlt.transformer(name="transform_contacts_csv_to_sf")
        def transformer(records: Iterator[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
            # Materialize list for resolution
            records_list = list(records)  
            if not records_list:
                return

            # Validate Schema
            required_columns = ["Customer_Id", "First_Name", "Last_Name", "Email"]
            missing = [col for col in required_columns if col not in records_list[0]]
            if missing:
                raise ValueError(f"Missing required columns: {missing}")

            # Initialize Resolver using credentials already set by BasePipeline
            resolver = SalesforceKeyResolver(credentials=self.sf_credential_path)
            account_sobject = "Account"
            account_key_field = "Customer_ID__c"
            
            # Extract unique values
            account_key_values = {
                str(record["Customer_Id"]) 
                for record in records_list 
                if record.get("Customer_Id")
            }
            
            resolver.set_definition(
                sobject=account_sobject, 
                key_field=account_key_field, 
                key_values=list(account_key_values)
            )

            # Map fields
            for record in records_list:                
                yield { 
                    "FirstName": record["First_Name"],
                    "LastName": record["Last_Name"],
                    "Email": record["Email"],
                    "AccountId" : resolver.try_resolve(account_sobject, account_key_field, str(record["Customer_Id"]))
                }

        # Step 3: Apply Hints to the transformer
        transformer_resource = transformer
        transformer_resource.apply_hints(
            table_name="Contact",
            primary_key="Email",
            write_disposition="append",
            additional_table_hints={
                "x-salesforce-operation": "upsert",
            },
        )

        # Step 4: Build and Run Pipeline
        pipeline = dlt.pipeline(
            pipeline_name=self.pipeline_name,
            destination=salesforce_bulk2(credentials=self.sf_credential_path),
            dataset_name="contacts"
        )
        
        load_info = pipeline.run(source_resource | transformer_resource)
        print(f"Load details for {self.pipeline_name}:\n{load_info}")

if __name__ == "__main__":
    UpsertContactPipeline.main(
        pipeline_base_name="sample_upsert_contacts_csv_to_sf",
        default_csv_path="data/updated_contacts.csv",
        default_env="dev"
    )