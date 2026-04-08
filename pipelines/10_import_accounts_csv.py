"""
Sample pipeline upserting accounts from a CSV file to Salesforce
Using
- BasePipeline component,
- SalesforceBulk2 Destination with an upsert operation

Process:
- CSV File is loaded ( sample is data/upsert_accounts.csv )
- Accounts are transformed in the pipeline (mapping CSV columns into Salesforce fields)
- Accounts are upserted to Salesforce based the AccountID stored in ExternalId__c custom field

Prerequisites before execution
- Salesforce connection configured ( to a sandbox)
- A custom field on Account, named "ExternalId__c" and marked as External Id (preferrably)
"""

from _collections_abc import Iterator
from typing import Any

import dlt

from stairway_to_salesforce.components import BasePipeline
from stairway_to_salesforce.destinations import get_sf_bulk2_destination


# --- Pipeline configuration ---
PIPELINE_NAME = "sample_upsert_account_csv_to_sf"
DEFAULT_CSV_PATH = "pipelines/sample_data/updated_accounts.csv"
DEFAULT_VERBOSE = True
# ------------------------------


class AccountCsvPipeline(BasePipeline):
    def execute(self) -> None:
        # Step 1: Init pipeline
        pipeline = dlt.pipeline(
            pipeline_name=self.pipeline_name,
            destination=get_sf_bulk2_destination(credentials=self.sf_credential_path),
            dataset_name="accounts_data",
        )

        # Step 2: Source (from CSV file path given as input)
        source_resource = self.build_csv_source()

        # Step 3: Transform
        @dlt.transformer(name="transform_accounts_csv_to_sf")
        def transformer(records: Any) -> Iterator[dict[str, Any]]:
            # Ensure we are working with an iterable of records
            if isinstance(records, dict):
                resolved_records = [records]
            else:
                resolved_records = records

            # Maps CSV columns with SF fields
            # You could add consistency check or default value
            for record in resolved_records:
                yield {
                    "ExternalID__c": record.get("AccountID"),
                    "AccountNumber": record.get("AccountID"),
                    "Name": record.get("Name"),
                    "Type": record.get("Type"),
                    "Industry": record.get("Industry"),
                    "AnnualRevenue": record.get("AnnualRevenue"),
                    "NumberOfEmployees": record.get("NumberOfEmployees"),
                    "Phone": record.get("Phone"),
                    "Website": record.get("Website"),
                    "BillingStreet": record.get("BillingStreet"),
                    "BillingCity": record.get("BillingCity"),
                    "BillingPostalCode": record.get("BillingPostalCode"),
                    "BillingCountry": record.get("BillingCountry"),
                    "ShippingCity": record.get("ShippingCity"),
                    "Rating": record.get("Rating"),
                    "Description": record.get("Description"),
                }

        # Step 4: Destination (by configuring the transformer)
        transformer_resource = transformer
        transformer_resource.apply_hints(
            table_name="Account",
            primary_key="ExternalID__c",
            write_disposition="append",
            additional_table_hints={"x-salesforce-operation": "upsert"},
        )

        # Step 5: Run the pipeline
        self.run_pipeline(pipeline, source_resource | transformer_resource)


if __name__ == "__main__":
    AccountCsvPipeline.main(
        pipeline_base_name=PIPELINE_NAME,
        default_csv_path=DEFAULT_CSV_PATH,
        default_verbose=DEFAULT_VERBOSE,
    )
