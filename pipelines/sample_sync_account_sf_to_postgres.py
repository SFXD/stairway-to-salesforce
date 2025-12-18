#!/usr/bin/env python3
"""
Pipeline to sync Salesforce Account data to PostgreSQL.
Reworked to use BasePipeline for standardized CLI and environment management.
"""
import dlt
from dlt_salesforce_advanced.sources import salesforce_bulk2_source
from dlt_salesforce_advanced.components import BasePipeline


class SyncAccountSfToPostgresPipeline(BasePipeline):
    """
    Defines the logic to sync Salesforce SObjects to a PostgreSQL destination.
    """

    def execute(self) -> None:
        """
        Implementation of the Salesforce to Postgres sync logic.
        """
        target_schema = "public"
        
        # Preserved resource configurations from original sample
        resource_configs = [
            {
                "target_name": "tb_accounts",
                "target_primary_key": "account_id",
                "source_sobject": "Account",
                "write_disposition": "merge",
                "fields": {
                    "Id": "account_id",
                    "Name": "account_name",
                    "LastModifiedDate": "sf_modification_date",
                    "Description": "Description",
                    "CreatedDate": "CreatedDate",
                    "CurrencyIsoCode": "CurrencyIsoCode",
                    "Website": "Website",
                    "Owner.Name": "sf_owner"
                },
                "source_replication_key": "LastModifiedDate",
                "target_column_types": {
                    "website": {"data_type": "text"}
                },
                "source_query_filter": None
            }
        ]
        
        # Use inherited credential paths based on the environment (--env)
        # Note: self.sf_credential_path is automatically set to "salesforce.{env}"
        target_credentials_path = f"postgres.{self.env}"
        target_credentials = dlt.secrets[target_credentials_path]

        # Build pipeline using preserved names
        pipeline = dlt.pipeline(
            pipeline_name=self.pipeline_name,
            destination=dlt.destinations.postgres(credentials=target_credentials),
            dataset_name=target_schema
        )
        
        # Run the sync
        load_info = pipeline.run(
            salesforce_bulk2_source(resource_configs, credentials=self.sf_credential_path)
        )
        
        print(f"Sync complete for {self.pipeline_name}:")
        print(load_info)

if __name__ == "__main__":
    SyncAccountSfToPostgresPipeline.main(
        pipeline_base_name="sample_sync_account_sf_to_postgres",
        default_env="dev"
    )
