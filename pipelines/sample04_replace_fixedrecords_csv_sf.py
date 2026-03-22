#!/usr/bin/env python3
"""
Sample pipeline replacing all fixed records from a CSV file to Salesforce
- Using BasePipeline component and SalesforceBulk2 Destination with an upsert operation
- Showcasing Transform

Note on Salesforce destination:
Fixed record is a sample custom sobject (for security purpose).

To test the pipeline, you will either
- need to change the configuration to an existing sobject(existing records will be deleted)
- or to create the Fixed Record Sobject as the following:
    - Sobject Name: FixedRecord__c
    - Fields: Name, FixedCode__c, FixedDescription__c

Process:
- CSV File is loaded ( sample is data/all_fixed_records.csv )
- Fixed records are transformed in the pipeline
    - renaming columns
- Fixed records are loaded to Salesforce with a replace operation
"""

from _collections_abc import Iterator
from typing import Any

import dlt

from stairway_to_salesforce.components import BasePipeline
from stairway_to_salesforce.destinations import get_sf_bulk2_destination


# --- Pipeline configuration ---
PIPELINE_NAME = "sample_replace_fixedrecord_csv_to_sf"
DEFAULT_CSV_PATH = "pipelines/sample_data/all_fixed_records.csv"
DEFAULT_VERBOSE = True
# ---------------------------------


class SamplePipeline(BasePipeline):
    def execute(self) -> None:
        # Step 1: Init pipeline
        pipeline = dlt.pipeline(
            pipeline_name=self.pipeline_name,
            destination=get_sf_bulk2_destination(credentials=self.sf_credential_path),
            dataset_name="fixedrecords",
        )

        # Step 2: Source (from CSV file path given as input)
        source_resource = self.build_csv_source()

        # Step 3: Transform
        @dlt.transformer(name="transform_fixedrecords_csv_to_sf")
        def transformer(records: Any) -> Iterator[dict[str, Any]]:
            # Ensure we are working with an iterable of records
            if isinstance(records, dict):
                resolved_records = [records]
            else:
                resolved_records = records

            # Validate Schema
            required_columns = ["name", "code", "description"]
            missing = [col for col in required_columns if col not in resolved_records[0]]
            if missing:
                raise ValueError(f"Missing required columns: {missing}")

            # Map fields
            for record in resolved_records:
                yield {
                    "Name": record["name"],
                    "FixedCode__c": record["code"],
                    "FixedDescription__c": record["description"],
                }

        # Step 4: Destination
        transformer_resource = transformer
        transformer_resource.apply_hints(
            # SObject name
            table_name="FixedRecord__c",
            # Replace will execute a first delete operation and an insert
            write_disposition="replace",
        )

        # Step 5: Run the pipeline
        self.run_pipeline(pipeline, source_resource | transformer_resource)


if __name__ == "__main__":
    SamplePipeline.main(
        pipeline_base_name=PIPELINE_NAME,
        default_csv_path=DEFAULT_CSV_PATH,
        default_verbose=DEFAULT_VERBOSE,
    )
