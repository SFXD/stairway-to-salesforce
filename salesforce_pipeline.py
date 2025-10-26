#!/usr/bin/env python3
"""Pipeline to load Salesforce data."""
import dlt
from sources.salesforce_bulk2 import salesforce_bulk2_source, build_resource


def load() -> None:

    accounts = build_resource(
        sobject="Account",
        fields=["Id", "Name", "LastModifiedDate"],
        primary_key="Id",
        #replication_key= "LastModifiedDate",
        #write_disposition="merge"
    )

    """Execute a pipeline from Salesforce."""    

    pipeline = dlt.pipeline(
        pipeline_name="salesforce", destination='postgres', dataset_name="salesforce_data"
    )
    # Execute the pipeline
    load_info = pipeline.run([accounts])

    # Print the load info
    print(load_info)


if __name__ == "__main__":
    load()
