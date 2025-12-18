#!/usr/bin/env python3
"""
Delete contacts from a csv file, based on an external key "Email" 

The delete operation is resolving the email into Salesforce Id (necessary for the salesforce delete)
"""
import dlt
from dlt.sources.filesystem import filesystem, read_csv
from dlt_salesforce_advanced.destinations import salesforce_bulk2
from dlt_salesforce_advanced.components import BasePipeline

class DeleteContactPipeline(BasePipeline):
    def execute(self) -> None:     
        ### Step 1: Source
        source_resource = filesystem(
            bucket_url=self.csv_file_path.rsplit('/', 1)[0],  # folder path
            file_glob=self.csv_file_path.rsplit('/', 1)[1]   # filename
        ) | read_csv()

        ### Step 2:  Set destination format (without transformation)
        source_resource.apply_hints(
            table_name="Contact",
            primary_key="Email",
            write_disposition="append",
            additional_table_hints={
                "x-salesforce-operation": "delete",   # custom hint
            },
        )

        ### Step 3  Destination
        destination_resource = salesforce_bulk2(credentials=self.sf_credential_path)

        ### Step 4:  Build the pipeline
        pipeline = dlt.pipeline(
            pipeline_name=f"{self.pipeline_name}",
            destination=destination_resource,
            dataset_name="contacts"
        )
        
        ### Step 5 : run pipeline
        load_info = pipeline.run(source_resource)

        ### Step 6 : post process
        print(f"  {load_info}")


if __name__ == "__main__":
    DeleteContactPipeline.main(
        pipeline_base_name="sample_delete_contacts_csv_to_sf",
        default_csv_path="data/deleted_contacts.csv",
        default_env="dev"
    )