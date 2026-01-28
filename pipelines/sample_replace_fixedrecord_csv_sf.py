#!/usr/bin/env python3
"""
Sample pipeline replacing all fixed records from a CSV file to Salesforce
- Using BasePipeline component and SalesforceBulk2 Destination with an upsert operation
- Showcasing Transform

Note on Salesforce destination:
Fixed record is a sample custom sobject (for security purpose to avoid unvolontary sample pipeline launch). 
To test the pipeline, you will either need to change the configuration to an existing sobject (watch out, as existing records will be deleted)
or to create the Fixed Record Sobject as the following:
- Sobject Name: FixedRecord__c 
- Fields: Name, FixedCode__c, FixedDescription__c


Process:
- CSV File is loadded ( sample is data/all_fixed_records.csv )
- Fixed records are transformed in the pipeline
    - renaming columns
- Fixed records are loaded to Salesforce with a replace operation ( deleting all records and loading the new ones)

"""
from typing import Iterator, Dict, Any

import dlt
from dlt.sources.filesystem import filesystem, read_csv

from dlt_salesforce_advanced.destinations import salesforce_bulk2
from dlt_salesforce_advanced.components import BasePipeline

class ReplaceFixedRecordPipeline(BasePipeline):
    def execute(self) -> None:
        """
        Implementation of the DLT pipeline steps.
        """
        # Step 1: Init pipeline
        pipeline = dlt.pipeline(
            pipeline_name=self.pipeline_name,
            destination=salesforce_bulk2(credentials=self.sf_credential_path),
            dataset_name="fixedrecords"
        )

        # Step 2: Source
        source_resource = filesystem(
            bucket_url=self.csv_file_path.rsplit('/', 1)[0],
            file_glob=self.csv_file_path.rsplit('/', 1)[1]
        ) | read_csv()

        # Step 3: Transform
        @dlt.transformer(name="transform_fixedrecords_csv_to_sf")
        def transformer(records: Iterator[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
            # Safety if the records are processed one by one
            if isinstance(records,dict):
                records=[records]

            # Validate Schema
            required_columns = ["name", "code", "description"]
            missing = [col for col in required_columns if col not in records[0]]
            if missing:
                raise ValueError(f"Missing required columns: {missing}")

            # Map fields
            for record in records:                
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
            write_disposition="replace"         # Replace will execute a first delete bulk2 operation on the Sobject and then reload the data
        )

        # Step 5: Run pipeline        
        load_info = pipeline.run(source_resource | transformer_resource)
        print(f"Load details for {self.pipeline_name}:\n{load_info}")

if __name__ == "__main__":
    ReplaceFixedRecordPipeline.main(
        pipeline_base_name="sample_replace_fixedrecord_csv_to_sf",
        default_csv_path="data/all_fixed_records.csv",
        default_env="dev"
    )