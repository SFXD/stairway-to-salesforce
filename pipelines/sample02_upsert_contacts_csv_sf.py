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

from _collections_abc import Iterator
from typing import Any

import dlt

from stairway_to_salesforce.components import BasePipeline, SalesforceKeyResolver
from stairway_to_salesforce.destinations import get_sf_bulk2_destination


# --- Pipeline configuration ---
PIPELINE_NAME = "sample_upsert_contacts_csv_to_sf"
DEFAULT_CSV_PATH = "pipelines/sample_data/updated_contacts.csv"
DEFAULT_VERBOSE = True
# ------------------------------


class SamplePipeline(BasePipeline):
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
            dataset_name="contacts_data",
        )

        # Step 2: Source (from CSV file path given as input)
        source_resource = self.build_csv_source()

        # Step 3: Transform
        @dlt.transformer(name="transform_contacts_csv_to_sf")
        def transformer(records: Any) -> Iterator[dict[str, Any]]:
            # Ensure we are working with an iterable of records
            if isinstance(records, dict):
                resolved_records = [records]
            else:
                resolved_records = records

            # Extract source external keys we need to convert into Salesforce Ids
            account_key_values = {
                str(record["AccountID"]) for record in resolved_records if record.get("AccountID")
            }

            # Init resolver ( with base pipeline credentials)
            resolver = SalesforceKeyResolver(credentials=self.sf_credential_path)
            account_sobject = "Account"
            account_key_field = "ExternalID__c"  # sample custom field on Account
            resolver.set_definition(
                sobject=account_sobject,
                key_field=account_key_field,
                key_values=account_key_values,
            )

            # Map CSV columns with SF field
            # You could add additional csv column mapping (some are ignored)
            for record in resolved_records:
                yield {
                    # Direct field mapping
                    "FirstName": record["FirstName"],
                    "LastName": record["LastName"],
                    "Email": record["Email"],
                    # Field mapping with External ID resolution
                    "AccountId": resolver.try_resolve(
                        account_sobject, account_key_field, str(record["AccountID"])
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

        # Step 5: Run the pipeline
        self.run_pipeline(pipeline, source_resource | transformer_resource)


if __name__ == "__main__":
    SamplePipeline.main(
        pipeline_base_name=PIPELINE_NAME,
        default_csv_path=DEFAULT_CSV_PATH,
        default_verbose=DEFAULT_VERBOSE,
    )
