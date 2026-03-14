# Stairway to Salesforce

[![CI](https://github.com/SFXD/stairway-to-salesforce/actions/workflows/ci.yml/badge.svg)](https://github.com/SFXD/stairway-to-salesforce/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/SFXD/stairway-to-salesforce/branch/main/graph/badge.svg)](https://codecov.io/gh/SFXD/stairway-to-salesforce)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/SFXD/stairway-to-salesforce)](LICENSE)

A simple ETL Python Framework for Salesforce, built on DLT, featuring Bulk API v2 connectors and a Salesforce Key Resolver for external ID conversion.

## Features

- **Simple pipeline definition** using DLT framework 
- **Salesforce Bulk API v2** source and destination connectors
- **Compatible with DLT connectors** both official and from the community
- **Full compatibility with DLT functionalities** for credentials, schema validation, performance, memory...
- **Salesforce Key Resolver** - Convert external IDs to Salesforce IDs (useful for lookup or delete based on external id)
- **Simplified Salesforce environment management** to differenciate test environment credentials from production credentials
- **Compatibility with Apache Airflow** for orchestration and scheduling

## Quick Install

For normal usage, and basic CSV sample pipelines
```bash
pip install uv
uv sync 
```

If you want to test the sample pipeline Salesforce to Postgres, you have to add postgres dependency (dlt[postgres]) as follow 
```bash
uv sync --extra postgres
```

## Quick Example

The following example show the simple structure of a pipeline with 5 steps.
Fully working samples can be found in pipelines folder.

```python
import dlt
from stairway_to_salesforce.components import BasePipeline

class HelloSalesforcePipeline(BasePipeline):

    def execute(self) -> None:
        # Step 1: Init pipeline with destination 
        pipeline = dlt.pipeline(
            pipeline_name=self.pipeline_name,
            destination= ... using DLT connectors or Salesforce Bulk2 ...
            dataset_name="..."
        )   

        # Step 2: Source
        source_resource = ... using DLT connectors or Salesforce Bulk2 ...

        # Step 3: Transform 
        @dlt.transformer(name="...")
        def transformer(records: Iterator[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
            ...
            yield ... record by record with data transformation ...

        # Step 4: Destination (by configuring the transformer)
        transformer_resource = transformer
        transformer_resource.apply_hints(            
            table_name="... table or sobjectname for Salesforce Bulk2 ...",
            primary_key="... key column /field ...",               
            ...
        )

        # Step 5: Execute pipeline
        load_info = pipeline.run(source_resource | transformer_resource)
        print(f"Load details for {self.pipeline_name}:\n{load_info}")

if __name__ == "__main__":
    HelloSalesforcePipeline.main(
        pipeline_base_name="hello_salesforce",
        default_env="dev"   # default environment if not specified on runtime
    )
```

## 📚 Full Documentation

**Complete documentation available at: [https://sfxd.github.io/stairway-to-salesforce/](https://sfxd.github.io/stairway-to-salesforce/)**

- [Getting Started](https://sfxd.github.io/stairway-to-salesforce/getting-started/)
- [Examples & Tutorials](https://sfxd.github.io/stairway-to-salesforce/examples/)
- [API Reference](https://sfxd.github.io/stairway-to-salesforce/api-reference/)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

See [LICENSE](LICENSE) file for details.

## Troubleshooting

### pyarrow timezone error (Windows)
If you encounter timezone-related errors with pyarrow on Windows, run:
    uv add tzdata

Then set the following environment variable in your `.env` or shell :
    TZDIR=<path_to_tzdata_zoneinfo>