#!/usr/bin/env python3
"""
Delete contacts from a csv file, based on an external key "Email"

The delete operation is resolving the email into Salesforce Id (necessary for the salesforce delete)
"""

import dlt

from stairway_to_salesforce.components import BasePipeline
from stairway_to_salesforce.destinations import get_sf_bulk2_destination


# --- Pipeline configuration ---
PIPELINE_NAME = "sample_delete_contacts_csv_to_sf"
DEFAULT_CSV_PATH = "pipelines/sample_data/deleted_contacts.csv"
DEFAULT_VERBOSE = True
# ---------------------------------


class RecordDeletionPipeline(BasePipeline):
    def execute(self) -> None:
        # Step 1: Init pipeline
        pipeline = dlt.pipeline(
            pipeline_name=self.pipeline_name,
            destination=get_sf_bulk2_destination(credentials=self.sf_credential_path),
            dataset_name="contact_deletion",
        )

        # Step 2: Source (from CSV file path given as input)
        source_resource = self.build_csv_source()

        # Step 3: Transform
        # No transform needed

        # Step 4 Destination
        # Directly applied to the source_resource as we don't have a transformer here
        source_resource.apply_hints(
            table_name="Contact",  # Target SObject Name
            primary_key="Email",  # Email will be converted in Id by Salesforce Key Resolver
            write_disposition="append",  # Default write disposition
            additional_table_hints={
                "x-salesforce-operation": "delete",  # Delete job on Bulk API2
            },
        )

        # Step 5: Run the pipeline
        self.run_pipeline(pipeline, source_resource)


if __name__ == "__main__":
    RecordDeletionPipeline.main(
        pipeline_base_name=PIPELINE_NAME,
        default_csv_path=DEFAULT_CSV_PATH,
        default_verbose=DEFAULT_VERBOSE,
    )
