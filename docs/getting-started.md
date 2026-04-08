# Getting Started

This guide will walk you through the initial configuration of **Stairway to Salesforce** and the first run of a sample pipeline.

## 0. Prerequisites
* **Python 3.12+**: The framework leverages modern type hinting and syntax.
* **uv**: (Highly recommended) Fast Python package manager. [Install it here](https://docs.astral.sh/uv/getting-started/installation/).
* **Git**: To clone the repository (as the project is not yet on PyPI).

## 1. Install the project

```bash
# Clone the repository
git clone https://github.com/SFXD/stairway-to-salesforce.git
cd stairway-to-salesforce

# Setup the project
uv sync
```

:bulb: You can add additional [DLT verified source (SQL databases, REST APIs, Cloud Storage)](https://dlthub.com/docs/dlt-ecosystem/verified-sources)
```bash
# Connector postgres
uv add "dlt[postgres]"
```

> **Windows Note:** If you encounter timezone-related errors with PyArrow, run `uv add tzdata` and set the `TZDIR` environment variable to the tzdata zoneinfo folder.

## 2. Prepare your Salesforce sandbox

**We strongly recommend you to first connect to a sandbox and always test your pipeline against a non-production environment**

Before to run the first pipeline, you need to configure a few things within your Salesforce :

* **Account External Key field on Account** : Create a text custom field `ExternalId__c` (Text, Unique, External ID) on the **Account** object.
* **Configure an external app** and keep the client id and client secret for the next step - [Salesforce help](https://help.salesforce.com/s/articleView?id=xcloud.external_client_apps.htm&type=5)

## 3. Connect your Salesforce sandbox

In this section, we assume that you are working in a non-production environments, like a sandbox.
If you want to configure the connection with your production environment, do the same below [salesforce.production].

* Rename or copy `.dlt/secrets.toml.example` as `.dlt/secrets.toml`
* Open it and identify the salesforce section [salesforce.dev]
```toml
[salesforce.dev]
client_id = "..."
client_secret = "..."
domain = "..."
```
* Update the credentials within `.dlt/secrets.toml`.

:warning: This setup is not recommended for a production setup.
* Credential storages, such as environment variables : [DLT credential setup page](https://dlthub.com/docs/general-usage/credentials/setup).
* Authentication flows, such as JWT Auth flow : [Authentication flows](authentication.md)

## 4. Run the pipeline

This pipeline will show you how to run a complete prospecting pipeline: fetching live tech companies from the French Government API and upserting them directly into your Salesforce sandbox as Accounts. It’s the perfect way to test the framework's power with real-world data in seconds.

```bash
uv run pipelines/01_get_prospects_from_api.py --env dev
```

**Notes**: This commands targets explicitly the dev environment through the --env parameter. Even if omitted, it will be dev by default ( by security ).

⚠️ **Data Responsibility:** This sample fetches data from the Annuaire des Entreprises (INSEE/INPI). These records are provided under the Open Licence 2.0. While this pipeline includes GDPR filters (excluding non-public and individual entrepreneurs), you remain responsible for the compliance and legal usage of the data once stored in your Salesforce instance.


### 5. Review

The tech companies fetched from the French Government API are now upserted into your Salesforce sandbox as Accounts. You can verify the results by searching for accounts with the Type "Prospect" or by checking the ExternalId__c field.
The data volume is limited to the first page (of the API) with a maximum of 25 records, limited to only public data, filtering out "Individual Entrepreneurs".

💡 **This flagship sample demonstrates a complete "API-to-Salesforce" flow. You can now adapt this pattern to connect Salesforce with any [DLT verified source (SQL databases, REST APIs, Cloud Storage)](https://dlthub.com/docs/dlt-ecosystem/verified-sources) using the same standardized 5-step logic.**

⚠️ **Data Responsibility:** This sample fetches data from the Annuaire des Entreprises (INSEE/INPI). These records are provided under the Open Licence 2.0. While this pipeline includes GDPR filters (excluding non-public and individual entrepreneurs), you remain responsible for the compliance and legal usage of the data once stored in your Salesforce instance.

:bulb: The repository has more sample pipelines for you to play with.  Please check **[Examples](examples.md)**.

## 6. Build your own
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

---

## Next Steps

* **[Examples](examples.md)**: Explore different pipeline types (Sync, Upsert, Delete).
* **[What is DLT?](dlt-overview.md)**: Learn more about the engine powering this framework.
* **[API Reference](api-reference.md)**: Consult the detailed documentation for components.
* **[Contributing](contributing.md)**: If you want to improve the framework or add new features.
