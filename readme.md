# Stairway to Salesforce

<!-- --8<-- [start:intro]-->
[![CI](https://github.com/SFXD/stairway-to-salesforce/actions/workflows/ci.yml/badge.svg)](https://github.com/SFXD/stairway-to-salesforce/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/SFXD/stairway-to-salesforce/branch/main/graph/badge.svg)](https://codecov.io/gh/SFXD/stairway-to-salesforce)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/SFXD/stairway-to-salesforce)](LICENSE)

A simple ETL Python Framework for Salesforce, built on [DLT](https://dlthub.com/docs/intro), featuring Bulk API v2 connectors and utility components.


## The Value Proposition

DLT is a powerful open-source data loading library, but it was missing key Salesforce components out of the box:

- **Source & destination connectors** on standard Salesforce **Bulk API v2**
- A **Key Resolver** to convert external IDs into Salesforce IDs

Stairway to Salesforce fills that gap, while staying fully compatible with the DLT ecosystem.


## Features

- **Simple pipeline definition** using the DLT framework
- **Salesforce Bulk API v2** source and destination connectors
- **Compatible with all DLT connectors**, both official and community
- **Full DLT feature support** — credentials, schema validation, incremental loading, memory management
- **Salesforce Key Resolver** — convert external IDs to Salesforce IDs for lookups and deletes
- **Simplified environment management** — differentiate dev/test credentials from production
- **Apache Airflow compatible** for orchestration and scheduling
<!-- --8<-- [end:intro] -->


## Quick try

This section will cover how to quickly setup one of the sample pipeline to load accounts from a CSV file to your Salesforce sandbox.

### 1. Install

```bash
git clone [https://github.com/SFXD/stairway-to-salesforce.git](https://github.com/SFXD/stairway-to-salesforce.git)
cd stairway-to-salesforce
pip install uv
uv sync
```

### 2. Prepare your Salesforce sandbox

1. Account External Key field on Account : Create a text custom field `External_ID__c` (Text, Unique, External ID) on the **Account** object.
2. Integration user: configure the external user and make sur he can write accounts ( including the External_ID__c field).
3. Configure an external app and keep the client id and client secret for the next step


### 3. Connect your Salesforce Sandbox

Stairway to Salesforce uses DLT's native secret management.
For a quick connection, we are using secrets.toml file. (not recommended for production)

1. Rename or copy `.dlt/secrets.toml.example` to `.dlt/secrets.toml`.
2. Fill in your Salesforce credentials under the `[salesforce.dev]` section:

```toml
[salesforce.dev]
client_id = "..."
client_secret = "..."
domain = "..."
```

### 4. Run the pipeline

Use `uv` to execute the pre-built script:

```bash
uv run pipelines/sample01_upsert_accounts_csv_sf.py --env dev
```

### 5. Review

The accounts defined in the sample csv file 'pipelines/sample_data/updated_accounts.csv' are now loaded in your sandbox.

💡 **Loading accounts from a CSV file to Salesforce is only a quick way to show the pipeline in action. You can now adapt it to use any [DLT source](https://dlthub.com/docs/dlt-ecosystem/verified-sources) or any [DLT destination](https://dlthub.com/docs/dlt-ecosystem/destinations).**


## Build your own
A pipeline follows a simple 5-step structure:

```python
import dlt
from stairway_to_salesforce.components import BasePipeline

class HelloSalesforcePipeline(BasePipeline):

    def execute(self) -> None:
        # Step 1: Init pipeline with destination
        pipeline = dlt.pipeline(
            pipeline_name=self.pipeline_name,
            destination= ... # Any destination from DLT or Salesforce Bulk2
            dataset_name="..."
        )

        # Step 2: Source
        source_resource = ... # Any source from DLT or Salesforce Bulk2

        # Step 3: Transform
        @dlt.transformer(name="...")
        def transformer(records: Iterator[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
            yield ... # record by record transformation

        # Step 4: Configure destination hints
        transformer_resource = transformer
        transformer_resource.apply_hints(
            table_name="...",
            primary_key="...",
        )

        # Step 5: Run the pipeline
        self.run_pipeline(pipeline, source_resource | transformer_resource)

if __name__ == "__main__":
    HelloSalesforcePipeline.main(
        pipeline_base_name="hello_salesforce",
        default_env="dev"
    )
```

## 📚 Full Documentation

**Complete documentation available at: [https://sfxd.github.io/stairway-to-salesforce/](https://sfxd.github.io/stairway-to-salesforce/)**

- [Getting Started](https://sfxd.github.io/stairway-to-salesforce/getting-started/)
- [Examples & Tutorials](https://sfxd.github.io/stairway-to-salesforce/examples/)
- [API Reference](https://sfxd.github.io/stairway-to-salesforce/api-reference/)

## Contributing

See [CONTRIBUTING.md](.github/contributing.md) for development setup and guidelines.

## License

Apache-2.0 -See [LICENSE](LICENSE) file for details.

## Troubleshooting

### pyarrow timezone error (Windows)
If you encounter timezone-related errors with pyarrow on Windows, run:
    uv add tzdata

Then set the following environment variable in your `.env` or shell :
    TZDIR=<path_to_tzdata_zoneinfo>
