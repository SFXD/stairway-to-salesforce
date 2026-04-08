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

This section will show you how to run a complete prospecting pipeline: fetching live tech companies from the French Government API and upserting them directly into your Salesforce sandbox as Accounts. It’s the perfect way to test the framework's power with real-world data in seconds.

### 0. Prerequisites

* **Python 3.12+**: The framework leverages modern type hinting and syntax.
* **uv**: (Highly recommended) Fast Python package manager. [Install it here](https://docs.astral.sh/uv/getting-started/installation/).
* **Git**: To clone the repository (as the project is not yet on PyPI).
* **Salesforce Sandbox/Org**: With API access enabled and an External App configured.

### 1. Install the project

```bash
# Clone the repository
git clone https://github.com/SFXD/stairway-to-salesforce.git
cd stairway-to-salesforce

# Sync dependencies and install the project in the local environment
uv sync
```

### 2. Prepare your Salesforce sandbox

* **Account External Key field on Account** : Create a text custom field `ExternalId__c` (Text, Unique, External ID) on the **Account** object.
* **Configure an external app** and keep the client id and client secret for the next step

### 3. Connect your Salesforce Sandbox

1. Rename or copy `.dlt/secrets.toml.example` to `.dlt/secrets.toml`.
2. Fill in your Salesforce credentials under the `[salesforce.dev]` section:

```toml
[salesforce.dev]
client_id = "..."
client_secret = "..."
domain = "..."
```

For other auth methods (JWT) or production storage, see [Full Documentation](https://sfxd.github.io/stairway-to-salesforce/getting-started/).

### 4. Run the pipeline

```bash
uv run pipelines/01_get_prospects_from_api.py --env dev
```

### 5. Review

The tech companies fetched from the French Government API are now upserted into your Salesforce sandbox as Accounts. You can verify the results by searching for accounts with the Type "Prospect" or by checking the ExternalId__c field.
The data volume is limited to the first page (of the API) with a maximum of 25 records, limited to only public data, filtering out "Individual Entrepreneurs".

💡 **This flagship sample demonstrates a complete "API-to-Salesforce" flow. You can now adapt this pattern to connect Salesforce with any [DLT verified source (SQL databases, REST APIs, Cloud Storage)](https://dlthub.com/docs/dlt-ecosystem/verified-sources) using the same standardized 5-step logic.**

⚠️ **Data Responsibility:** This sample fetches data from the Annuaire des Entreprises (INSEE/INPI). These records are provided under the Open Licence 2.0. While this pipeline includes GDPR filters (excluding non-public and individual entrepreneurs), you remain responsible for the compliance and legal usage of the data once stored in your Salesforce instance.


## 📚 Full Documentation

**Complete documentation available at: [https://sfxd.github.io/stairway-to-salesforce/](https://sfxd.github.io/stairway-to-salesforce/)**

- [Getting Started](https://sfxd.github.io/stairway-to-salesforce/getting-started/)
- [Examples & Tutorials](https://sfxd.github.io/stairway-to-salesforce/examples/)
- [API Reference](https://sfxd.github.io/stairway-to-salesforce/api-reference/)

## Contributing

See [CONTRIBUTING.md](.github/contributing.md) for development setup and guidelines.

## License

Apache-2.0 -See [LICENSE](LICENSE) file for details.
