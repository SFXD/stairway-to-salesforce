# Getting Started

## Prerequisites

- Python 3.9 or higher
- A Salesforce org with API access enabled

## Installation

```bash
pip install uv
git clone https://github.com/SFXD/stairway-to-salesforce.git
cd stairway-to-salesforce
uv sync
```

For the Salesforce to Postgres sample pipeline, add the PostgreSQL connector:

```bash
uv sync --extra postgres
```

> **Windows only:** If you encounter timezone-related errors with PyArrow, run `uv add tzdata` and set `TZDIR=<path_to_tzdata_zoneinfo>` in your environment.

---

## Connecting to Salesforce

### 1. Create your secrets file

DLT looks for credentials in `.dlt/secrets.toml`. Start from the provided sample:

```bash
mkdir -p .dlt
cp .dlt/secrets_sample.toml .dlt/secrets.toml
```

### 2. Choose a connection flow

Stairway to Salesforce supports three Salesforce authentication flows. Add the corresponding block to your `secrets.toml`:

=== "Client Credentials"

    Recommended for server-to-server integrations with a Connected App.

    ```toml
    [salesforce.dev]
    auth_type = "client_credentials"
    instance_url = "https://yourorg.my.salesforce.com"
    client_id = "your_client_id"
    client_secret = "your_client_secret"
    ```

=== "Password Flow"

    Suitable for quick setup and scripting. Requires username + password + security token.

    ```toml
    [salesforce.dev]
    auth_type = "password"
    instance_url = "https://yourorg.my.salesforce.com"
    client_id = "your_client_id"
    client_secret = "your_client_secret"
    username = "your_username"
    password = "your_password"
    security_token = "your_security_token"
    ```

=== "JWT Bearer"

    Best for production pipelines. Uses a private key instead of a password.

    ```toml
    [salesforce.dev]
    auth_type = "jwt"
    instance_url = "https://yourorg.my.salesforce.com"
    client_id = "your_client_id"
    username = "your_username"
    private_key_file = "path/to/your/key.pem"
    ```

For all available fields and options, refer to `stairway_to_salesforce/drivers/salesforce_driver/sfdriver_specs.py`.

### 3. Understand environments

Stairway to Salesforce uses credential suffixes to separate environments. The suffix in `secrets.toml` maps directly to the environment your pipeline runs against:

```toml
[salesforce.dev]        # development org
...

[salesforce.production] # production org
...
```

The active environment is set at runtime when launching a pipeline:

```bash
uv run pipelines/my_pipeline.py --env production
```

If no `--env` flag is provided, `dev` is used by default. This prevents accidental runs against production.

The same suffix system applies to any other destination you configure:

```toml
[postgres.dev]
database = "my_database"
username = "my_user"
password = "my_password"
host = "localhost"
port = 5432
```

---

## Run Your First Pipeline

Once credentials are in place, verify everything works by running one of the included samples:

```bash
uv run pipelines/sample_sync_account_sf_to_csv.py
```

A successful run prints load details to the console:

```
Load details for sample_sync_account_sf_to_csv:
Pipeline sample_sync_account_sf_to_csv completed in ...
```

---

## Next Steps

- [Examples](examples.md) — Explore the full set of sample pipelines
- [API Reference](api-reference.md) — Dive into sources, destinations, and the Key Resolver
- [What is DLT?](dlt-overview.md) — Understand the core concepts behind the framework