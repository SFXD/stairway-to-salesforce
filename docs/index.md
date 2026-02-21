# Stairway to Salesforce

[![CI](https://github.com/SFXD/stairway-to-salesforce/actions/workflows/ci.yml/badge.svg)](https://github.com/SFXD/stairway-to-salesforce/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/SFXD/stairway-to-salesforce/branch/main/graph/badge.svg)](https://codecov.io/gh/SFXD/stairway-to-salesforce)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/SFXD/stairway-to-salesforce)](LICENSE)

A simple ETL Python Framework for Salesforce, built on top of [DLT](https://dlthub.com/docs/intro), featuring Bulk API v2 connectors and a Key Resolver for external ID conversion.

---

## Why Stairway to Salesforce?

DLT is a powerful open-source data loading library, but it was missing key Salesforce components out of the box:

- Native **Bulk API v2** source and destination connectors
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

A pipeline follows a simple 5-step structure:

```python
import dlt
from stairway_to_salesforce.components import BasePipeline

class HelloSalesforcePipeline(BasePipeline):

    def execute(self) -> None:
        # Step 1: Init pipeline with destination
        pipeline = dlt.pipeline(
            pipeline_name=self.pipeline_name,
            destination= ... # DLT connector or Salesforce Bulk2
            dataset_name="..."
        )

        # Step 2: Source
        source_resource = ... # DLT connector or Salesforce Bulk2

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

---

## Next Steps

- [Getting Started](getting-started.md) — Installation, credentials, and your first pipeline
- [Examples](examples.md) — Full working pipeline samples
- [API Reference](api-reference.md) — Detailed component documentation
- [What is DLT?](dlt-overview.md) — DLT concepts and how they integrate with this framework