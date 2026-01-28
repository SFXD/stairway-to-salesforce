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

        # Step 1: Init pipeline
        pipeline = dlt.pipeline(
            pipeline_name=f"{self.pipeline_name}",
            destination=salesforce_bulk2(credentials=self.sf_credential_path),  # specific to environment defined on runtime
            dataset_name="contacts"
        )

        # Step 2: Source
        source_resource = filesystem(
            bucket_url=self.csv_file_path.rsplit('/', 1)[0],  # folder path
            file_glob=self.csv_file_path.rsplit('/', 1)[1]   # filename
        ) | read_csv()

        # Step 3: Transform
        # No transform needed

        # Step 4 Destination ( directly applied to the source_resource as we don't have a transformer here)
        source_resource.apply_hints(
            table_name="Contact",           # Target SObject Name
            primary_key="Email",            # Email will be converted in Id by Salesforce Key Resolver  ( additional API consumption, use directly with ID to avoid it)
            write_disposition="append",     # Default write disposition handled, specialized with the operation below
            additional_table_hints={
                "x-salesforce-operation": "delete",  # Will execute a delete job through the Bulk2 API
            },
        )
        
        # Step 5 : run pipeline
        load_info = pipeline.run(source_resource)
        print(f"Load details for {self.pipeline_name}:\n{load_info}")


if __name__ == "__main__":
    DeleteContactPipeline.main(
        pipeline_base_name="sample_delete_contacts_csv_to_sf",
        default_csv_path="sample_data/deleted_contacts.csv",
        default_env="dev"
    )