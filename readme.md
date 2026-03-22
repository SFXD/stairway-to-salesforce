# Stairway to Salesforce

--8<-- [start:intro]
[![CI](https://github.com/SFXD/stairway-to-salesforce/actions/workflows/ci.yml/badge.svg)](https://github.com/SFXD/stairway-to-salesforce/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/SFXD/stairway-to-salesforce/branch/main/graph/badge.svg)](https://codecov.io/gh/SFXD/stairway-to-salesforce)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/SFXD/stairway-to-salesforce)](LICENSE)

A simple ETL Python Framework for Salesforce, built on [DLT](https://dlthub.com/docs/intro), featuring Bulk API v2 connectors and utility components.

---

## The Value Proposition

DLT is a powerful open-source data loading library, but it was missing key Salesforce components out of the box:

- **Source & destination connectors** on standard Salesforce **Bulk API v2**
- A **Key Resolver** to convert external IDs into Salesforce IDs

Stairway to Salesforce fills that gap, while staying fully compatible with the DLT ecosystem.

---

## Features

- **Simple pipeline definition** using the DLT framework
- **Salesforce Bulk API v2** source and destination connectors
- **Compatible with all DLT connectors**, both official and community
- **Full DLT feature support** — credentials, schema validation, incremental loading, memory management
- **Salesforce Key Resolver** — convert external IDs to Salesforce IDs for lookups and deletes
- **Simplified environment management** — differentiate dev/test credentials from production
- **Apache Airflow compatible** for orchestration and scheduling
--8<-- [end:intro]

---

## Quick Install

```bash
pip install uv
uv sync
```

For the Salesforce to Postgres sample pipeline:

```bash
uv sync --extra postgres
```

---

## Quick Example

### Define the pipeline
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

        # Step 5: Execute
        load_info = pipeline.run(source_resource | transformer_resource)
        print(f"Load details for {self.pipeline_name}:\n{load_info}")

if __name__ == "__main__":
    HelloSalesforcePipeline.main(
        pipeline_base_name="hello_salesforce",
        default_env="dev"
    )
```

### Run the pipeline

Run the pipeline on the default environment ( DEV normally )

```bash
uv run pipelines/hello-salesforce-pipeline.py
```

Run the pipeline on a specific environment

```bash
uv run pipelines/hello-salesforce-pipeline.py --env prod
```

---

## 📚 Full Documentation

**Complete documentation available at: [https://sfxd.github.io/stairway-to-salesforce/](https://sfxd.github.io/stairway-to-salesforce/)**

- [Getting Started](https://sfxd.github.io/stairway-to-salesforce/getting-started/)
- [Examples & Tutorials](https://sfxd.github.io/stairway-to-salesforce/examples/)
- [API Reference](https://sfxd.github.io/stairway-to-salesforce/api-reference/)

## Contributing

See [CONTRIBUTING.md](.github/contributing.md) for development setup and guidelines.

## License

See [LICENSE](LICENSE) file for details.

## Troubleshooting

### pyarrow timezone error (Windows)
If you encounter timezone-related errors with pyarrow on Windows, run:
    uv add tzdata

Then set the following environment variable in your `.env` or shell :
    TZDIR=<path_to_tzdata_zoneinfo>