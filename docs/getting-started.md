# Getting Started

This guide will walk you through the installation and initial configuration of **Stairway to Salesforce**.

---

## Prerequisites
* **Python 3.9** or higher.
* API access to a Salesforce organization (Developer Edition, Sandbox, or Production).
* The **uv** tool installed on your machine. [uv official documentation](https://docs.astral.sh/uv/)

---

## Installation
```bash
# Clone the repository
git clone https://github.com/SFXD/stairway-to-salesforce.git
cd stairway-to-salesforce

# Install dependencies with uv
uv sync
```

To use the sample pipeline for PostgreSQL, add the specific connector:
```bash
uv sync --extra postgres
```

> **Windows Note:** If you encounter timezone-related errors with PyArrow, run `uv add tzdata` and set the `TZDIR` environment variable to the tzdata zoneinfo folder.

---

## Salesforce connection

To start simple, we are connecting an **External App** from a **Salesforce sandbox**, storing credentials in **secret.toml file**.
This setup is a simple example to start with and can be adapted:
- Credential storages, such as environment variables : [DLT credential setup page](https://dlthub.com/docs/general-usage/credentials/setup).
- Authentication flows, such as JWT Auth flow : [Authentication flows](authentication.md)

**Process:**
- Rename or copy `.dlt/secrets.toml.example` as `.dlt/secrets.toml`
- Open it and identify the salesforce section [salesforce.dev]
```toml
[salesforce.dev]
auth_type = "client_credentials"
instance_url = "https://yourorg.my.salesforce.com"
client_id = "your_client_id"
client_secret = "your_client_secret"
```
- Configure the external app within your Salesforce **Sandbox** : [Salesforce help](https://help.salesforce.com/s/articleView?id=xcloud.external_client_apps.htm&type=5)
- Update the credentials within `.dlt/secrets.toml`.

:bulb: **You have configured a connection to a "dev" salesforce sandbox, that can be used both as source and as destination.**

:warning: If you want to configure the connection with your production environment, do the same below [salesforce.production].
**We strongly recommend you to first connect to a sandbox and always test your pipeline against a non-production environment**

---

## First pipeline
The repository has sample pipelines for you to play with. 


### Understanding environments

The suffix used in the file (e.g., `.dev` or `.production`) is linked to the `--env` argument passed during execution:

```bash
# Uses [salesforce.production] in secrets.toml
uv run pipelines/my_pipeline.py --env production
```

**Note:** For security, if the --env is not specified, it gets the dev value. It means you have to run explicitly --env production to have a production pipeline.
---

### 5. Using Sample Data (Sample Data)
The repository includes a `sample_data/` folder containing pre-configured CSV files (e.g., `deleted_contacts.csv`). These files are used by default in demonstration pipelines to allow you to test features without preparing your own data.

```bash
uv run pipelines/sample_delete_contact_csv_sf.py
```
---

## Run your first Pipeline
Once your credentials are configured, test the connection with a simple example that extracts Salesforce accounts to a local file:

```bash
uv run pipelines/sample_sync_account_sf_to_postgres.py
```

If the configuration is correct, you will see a load summary displayed in your console.

---

## Next Steps

* **[Examples](examples.md)**: Explore different pipeline types (Sync, Upsert, Delete).
* **[What is DLT?](dlt-overview.md)**: Learn more about the engine powering this framework.
* **[API Reference](api-reference.md)**: Consult the detailed documentation for components.