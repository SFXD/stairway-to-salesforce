"""
Sample pipeline upserting accounts from French Government API to Salesforce
Using
- BasePipeline component,
- SalesforceBulk2 Destination with an upsert operation

Process:
- Data is fetched from French Government API (via sample_sources.french_gov)
- Accounts are transformed in the pipeline (mapping API JSON into Salesforce fields)
- Accounts are upserted to Salesforce based on the SIREN stored in ExternalID__c

Prerequisites before execution:
- Salesforce connection configured
- A custom field on Account, named "ExternalID__c" marked as External Id
"""

from _collections_abc import Iterator
from typing import Any

import dlt

# Import the source from your new sample_sources folder
from sample_sources.api_french_gov import french_gov_source

from stairway_to_salesforce.components import BasePipeline
from stairway_to_salesforce.destinations import get_sf_bulk2_destination


# --- Pipeline configuration ---
PIPELINE_NAME = "sample_upsert_api_gouv_to_sf"
DEFAULT_VERBOSE = True
# ------------------------------


class ProspectsApiPipeline(BasePipeline):
    def execute(self) -> None:
        # Step 1: Init pipeline
        pipeline = dlt.pipeline(
            pipeline_name=self.pipeline_name,
            destination=get_sf_bulk2_destination(credentials=self.sf_credential_path),
            dataset_name="api_prospecting_data",
        )

        # Step 2: Source (calling french_gov_source without default values)
        # We specify the parameters explicitly as required by the sample source definition
        source_resource = french_gov_source(
            resource_name="lyon_tech_prospects",
            postcode="69002",
            sector="J",  # Information and Communication
        )

        # Step 3: Transform (Mapping API JSON to SF fields)
        @dlt.transformer(name="transform_api_to_sf")
        def transformer(records: Any) -> Iterator[dict[str, Any]]:
            # Ensure we are working with an iterable of records
            if isinstance(records, dict):
                resolved_records = [records]
            else:
                resolved_records = records

            for record in resolved_records:
                siren = record.get("siren")
                if not siren:
                    continue

                siege = record.get("siege", {})

                yield {
                    "ExternalID__c": siren,
                    "AccountNumber": siren,
                    "Name": record.get("nom_complet"),
                    "Type": "Prospect",
                    "Industry": "Technology",
                    "BillingStreet": (
                        f"{siege.get('numero_voie', '')}"
                        f"{siege.get('type_voie', '')}"
                        f"{siege.get('libelle_voie', '')}"
                    ).strip(),
                    "BillingCity": siege.get("libelle_commune"),
                    "BillingPostalCode": siege.get("code_postal"),
                    "BillingCountry": "France",
                    "Description": (
                        f"Legal Nature: {record.get('nature_juridique')}"
                        "- Source: API Recherche Entreprises"
                    ),
                }

        # Step 4: Destination (by configuring the transformer)
        # We connect the source to the transformer
        transformer_resource = source_resource | transformer

        transformer_resource.apply_hints(
            table_name="Account",
            primary_key="ExternalID__c",
            write_disposition="append",
            additional_table_hints={"x-salesforce-operation": "upsert"},
        )

        # Step 5: Run the pipeline
        self.run_pipeline(pipeline, transformer_resource)


if __name__ == "__main__":
    ProspectsApiPipeline.main(
        pipeline_base_name=PIPELINE_NAME,
        default_verbose=DEFAULT_VERBOSE,
    )
