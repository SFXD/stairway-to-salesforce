# Getting Started

This guide will walk you through the installation and initial configuration of **Stairway to Salesforce**.

## Prerequisites
* **Python 3.9** or higher.
* API access to a Salesforce organization (Developer Edition, Sandbox, or Production).
* The **uv** tool installed on your machine. [uv official documentation](https://docs.astral.sh/uv/)
* Optional : **Make** installed (standard on Linux/macOS, available via Choco or WSL on Windows)

## 1. Installation

### Clone repo
```bash
# Clone the repository
git clone https://github.com/SFXD/stairway-to-salesforce.git
cd stairway-to-salesforce
```
### Setup environment
Choose the method that fits your workflow. Both methods install the framework and development tools (Ruff, Mypy).

**Option A: Recommended (Fastest)**
If you have make installed:
```bash
# Setup everything (dependencies + git hooks)
make install
```

**Option B: Manual setup**
If you prefer to run commands manually (without make):
```bash
pip install uv
uv sync
```

### Install additional DLT connectors
You can add additional DLT connectors such as postgres (useful for the sample pipeline 05 for example)
```bash
uv add "dlt[postgres]"
```

> **Windows Note:** If you encounter timezone-related errors with PyArrow, run `uv add tzdata` and set the `TZDIR` environment variable to the tzdata zoneinfo folder.

## 2. Salesforce connection

To start simple, we are connecting an **External App** from a **Salesforce sandbox**, storing credentials in **secret.toml file**.
This setup is a simple example to start with and can be adapted:

* Credential storages, such as environment variables : [DLT credential setup page](https://dlthub.com/docs/general-usage/credentials/setup).
* Authentication flows, such as JWT Auth flow : [Authentication flows](authentication.md)

### Disclaimer

**We strongly recommend you to first connect to a sandbox and always test your pipeline against a non-production environment**
In this section, we assume that you are working in a non-production environments, like a sandbox.

If you want to configure the connection with your production environment, do the same below [salesforce.production].

### Configuration

* Rename or copy `.dlt/secrets.toml.example` as `.dlt/secrets.toml`
* Open it and identify the salesforce section [salesforce.dev]
```toml
[salesforce.dev]
auth_type = "client_credentials"
instance_url = "https://yourorg.my.salesforce.com"
client_id = "your_client_id"
client_secret = "your_client_secret"
```

* Configure the external app within your Salesforce **Sandbox** : [Salesforce help](https://help.salesforce.com/s/articleView?id=xcloud.external_client_apps.htm&type=5)
* Update the credentials within `.dlt/secrets.toml`.

## 3. First pipeline: Upsert accounts from CSV to Salesforce

In this section, we will execute the sample01 to upsert accounts from the CSV file 'pipelines/sample_data/updated_accounts.csv' to your 'dev' salesforce.
It will create a few accounts into your org, based on the external id field "External_ID__c".

### Prerequisites

* Your salesforce sandbox is configured as salesforce.dev ( see previous section )
* Create a new text field "External_ID__c" on Account. You have to mark it as External Key and ideally as unique.

### Run the pipeline
Once your credentials are configured, test the connection with a simple example that upsert accounts from a CSV file (in Sample data) to your Salesforce environment

```bash
uv run pipelines/sample01_upsert_accounts_csv_sf.py --env dev --csv_file pipelines/sample_data/updated_accounts.csv
```

If the configuration is correct, you will see a load summary displayed in your console.

**Notes**: This commands defines explicitly the following parameters

* **--csv_file** <path>: a sample csv file in pipelines/sample_data. If omitted, the default value is the sample file ( configurable in the pipeline itself )
* **--env** dev: the target salesforce environment dev (as configured in your variables). If omitted, it will be dev by default ( by security ).

:bulb: The repository has sample pipelines for you to play with.

### Wrapping it up

The repository has more sample pipelines for you to play with.  Please check **[Examples](examples.md)**: Explore different pipeline types (Sync, Upsert, Delete).

---

## Next Steps

* **[Examples](examples.md)**: Explore different pipeline types (Sync, Upsert, Delete).
* **[What is DLT?](dlt-overview.md)**: Learn more about the engine powering this framework.
* **[API Reference](api-reference.md)**: Consult the detailed documentation for components.
* **[Contributing](contributing.md)**: If you want to improve the framework or add new features.
