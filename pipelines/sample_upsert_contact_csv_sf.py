#!/usr/bin/env python3
"""
Sample pipeline upserting contacts from a CSV file to Salesforce
Using
- BasePipeline component,
- SalesforceKeyResolver Component
- SalesforceBulk2 Destination with an upsert operation

Process:
- CSV File is loaded ( sample is data/upsert_contacts.csv )
- Contacts are transformed in the pipeline
    - keeping only specific columns (if additional columns are present in the csv)
    - resolving the Account Customer Id (a custom External Id field)  as a Salesforce Id
- Contacts are upserted to Salesforce based on the Email as External Id


"""

from typing import Any, Dict, Iterator

import dlt
from dlt.sources.filesystem import filesystem, read_csv

from stairway_to_salesforce.components import BasePipeline, SalesforceKeyResolver
from stairway_to_salesforce.destinations import get_sf_bulk2_destination


class UpsertContactPipeline(BasePipeline):
    """
    Defines the specific logic for upserting contacts from CSV to Salesforce.
    """

    def execute(self) -> None:
        """
        Implementation of the DLT pipeline steps.
        """
        # Step 1: Init pipeline
        pipeline = dlt.pipeline(
            pipeline_name=self.pipeline_name,
            destination=get_sf_bulk2_destination(credentials=self.sf_credential_path),
            dataset_name="contacts",
        )

        # Step 2: Source
        source_resource = (
            filesystem(
                bucket_url=self.csv_path.rsplit("/", 1)[0],
                file_glob=self.csv_path.rsplit("/", 1)[1],
            )
            | read_csv()  # noqa: W503
        )

        # Step 3: Transform
        @dlt.transformer(name="transform_contacts_csv_to_sf")
        def transformer(records: Any) -> Iterator[Dict[str, Any]]:
            # Ensure we are working with an iterable of records
            if isinstance(records, dict):
                resolved_records = [records]
            else:
                resolved_records = records

            # Validate source schema
            required_columns = [
                "External_ID",
                "First_Name",
                "Last_Name",
                "Email",
            ]  # required columns to be updated with your csv structure
            missing = [col for col in required_columns if col not in resolved_records[0]]
            if missing:
                raise ValueError(f"Missing required columns: {missing}")

            # Extract source external keys we need to convert into Salesforce Ids
            account_key_values = {
                str(record["External_ID"])
                for record in resolved_records
                if record.get("External_ID")
            }

            # Init resolver ( with base pipeline credentials)
            resolver = SalesforceKeyResolver(credentials=self.sf_credential_path)
            account_sobject = "Account"
            # For the sample, External_ID__c is an external key custom field on Account
            account_key_field = "External_ID__c"
            resolver.set_definition(
                sobject=account_sobject,
                key_field=account_key_field,
                key_values=list(account_key_values),
            )

            # Map fields
            for record in resolved_records:
                yield {
                    # Direct field mapping
                    "FirstName": record["First_Name"],
                    "LastName": record["Last_Name"],
                    "Email": record["Email"],
                    # Field mapping with External ID resolution
                    "AccountId": resolver.try_resolve(
                        account_sobject, account_key_field, str(record["External_ID"])
                    ),
                }

        # Step 4: Destination (by configuring the transformer)
        transformer_resource = transformer
        transformer_resource.apply_hints(
            table_name="Contact",  # Target sObject Name
            primary_key="Email",  # required for an append / upsert
            write_disposition="append",
            # Merge write_disposition is not handled,
            # append behavior is defined by the operation parameter below
            additional_table_hints={
                "x-salesforce-operation": "upsert",
                # Bulk2 operation : insert, update, upsert, delete
            },
        )

        # Step 5: Execute pipeline
        load_info = pipeline.run(source_resource | transformer_resource)
        print(f"Load details for {self.pipeline_name}:\n{load_info}")


if __name__ == "__main__":
    UpsertContactPipeline.main(
        pipeline_base_name="sample_upsert_contacts_csv_to_sf",
        default_csv_path="sample_data/updated_contacts.csv",
        default_env="dev",
    )
