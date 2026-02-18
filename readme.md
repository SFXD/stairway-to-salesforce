# Stairway to Salesforce

[![CI](https://github.com/SFXD/stairway-to-salesforce/actions/workflows/ci.yml/badge.svg)](https://github.com/SFXD/stairway-to-salesforce/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/SFXD/stairway-to-salesforce/branch/main/graph/badge.svg)](https://codecov.io/gh/SFXD/stairway-to-salesforce)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/SFXD/stairway-to-salesforce)](LICENSE)

A simple ETL Python Framework for Salesforce, built on top of DLT, featuring Bulk API v2 connectors and a Salesforce Key Resolver for external ID conversion.

## Features

- 🚀 **Salesforce Bulk API v2** source and destination connectors
- 🔑 **Salesforce Key Resolver** - Convert external IDs to Salesforce IDs
- 📊 **Multiple operations** - Insert, upsert, delete, and replace
- 🔄 **Incremental loading** - Efficient data synchronization
- 🛠️ **Built on DLT** - Leverage DLT's powerful data pipeline capabilities

## Quick Install

```bash
pip install uv
uv sync
```

## Quick Example

```python
from stairway_to_salesforce.components import BasePipeline

# Sync Salesforce accounts to Postgres
pipeline = BasePipeline("sync_accounts", environment="dev")
# ... configure source and destination
pipeline.run()
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