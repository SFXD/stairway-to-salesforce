#!/usr/bin/env python3
"""
Pipeline to sync Salesforce Account data to PostgreSQL.
Reworked to use BasePipeline for standardized CLI and environment management.
"""

from typing import Any, Dict, Iterator

import dlt

from stairway_to_salesforce.components import BasePipeline
from stairway_to_salesforce.sources import salesforce_bulk2_source


class SampleSyncAccountSfToPostgresPipeline(BasePipeline):
    """
    Defines the logic to sync Salesforce SObjects to a PostgreSQL destination.
    """

    def execute(self) -> None:
        """
        Implementation of the Salesforce to Postgres sync logic.
        """
        # Step 1: Init pipeline
        pipeline = dlt.pipeline(
            pipeline_name=self.pipeline_name,  # handle by base pipeline
            destination=dlt.destinations.postgres(
                credentials=self.get_credentials("postgres")
            ),  # get credentials based on the environment
            dataset_name="public",  # This is the schema with postgres
        )

        # Step 2: Source
        source_definition = [
            {
                "name": "sf_accounts",
                "write_disposition": "merge",
                "sobject": "Account",
                "primary_key": "Id",
                "replication_key": "LastModifiedDate",
                "query_filter": None,
                "fields": [
                    "Id",
                    "Name",
                    "LastModifiedDate",
                    "Description",
                    "CreatedDate",
                    "CurrencyIsoCode",
                    "Website",
                    "Owner.Name",
                ],
                "column_types": {"website": {"data_type": "text"}},
            }
        ]
        source_resource = salesforce_bulk2_source(
            source_definition, credentials=self.sf_credential_path
        )

        # Step 3: Transform
        @dlt.transformer(name="tb_accounts")
        def transformer(records: Any) -> Iterator[Dict[str, Any]]:
            # Ensure we are working with an iterable of records
            if isinstance(records, dict):
                resolved_records = [records]
            else:
                resolved_records = records

            for record in resolved_records:
                yield {
                    "account_id": record["Id"],
                    "account_name": record["Name"],
                    "Description": record["Description"],
                    "CreatedDate": record["CreatedDate"],
                    "CurrencyIsoCode": record["CurrencyIsoCode"],
                    "Website": record["Website"],
                    "sf_owner": record["Owner.Name"],
                }

        # Step 4: Destination
        transformer_resource = transformer
        transformer_resource.apply_hints(
            table_name="tb_accounts",
            primary_key="account_id",
            write_disposition="merge",
        )

        # Step 5: Run pipeline
        load_info = pipeline.run(source_resource | transformer_resource)
        print(f"Load details for {self.pipeline_name}:\n{load_info}")


if __name__ == "__main__":
    SampleSyncAccountSfToPostgresPipeline.main(
        pipeline_base_name="sample_sync_accounts_sf_to_postgres", default_env="dev"
    )
