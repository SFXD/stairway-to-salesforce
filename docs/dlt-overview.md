# What is DLT?

[DLT (Data Load Tool)](https://dlthub.com/docs/intro) is the open-source Python library that powers **Stairway to Salesforce**. It handles all the complex "plumbing" of ETL (Extract, Load, Transform) so you can focus on business logic.

---

## Core Concepts

### 1. Pipeline
The pipeline is the central object. It acts as a bridge between a source and a destination. It manages execution, state tracking, and automatic schema management.

```python
import dlt

pipeline = dlt.pipeline(
    pipeline_name="my_pipeline",
    destination="duckdb",
    dataset_name="my_dataset"
)
```

### 2. Resource
A resource is a function (often a generator) decorated with `@dlt.resource`. It is the basic unit for data extraction. It produces the data that will then be transformed or loaded.

```python
@dlt.resource(table_name="accounts")
def get_accounts():
    for record in my_source:
        yield record
```

### 3. Transformer
A transformer is a special resource that receives data from another resource to modify it. In **Stairway to Salesforce**, this is where you perform field renamings or ID resolutions via the `KeyResolver`.

---

## Advanced Features

### Write Disposition
The "write disposition" defines how data is integrated into the destination:

* **Append**: Simply adds new records after existing ones (ideal for logs or history).
* **Replace**: Empties the destination table and replaces it entirely with the newly provided data.
* **Merge**: Updates existing records and inserts new ones (Upsert) based on a primary key (`primary_key`).

### Schema & Data Types
DLT inspects your data in real-time and automatically generates the database structure:
* **Schema Evolution**: If you add a new field in your source (e.g., a column in a CSV), DLT will update the destination table automatically without manual intervention.
* **Type Conversion**: It detects and converts data types (e.g., transforming an ISO string into a proper SQL `Timestamp` type).

### Incremental Loading
This is one of DLT's major strengths. Using a `replication_key` (such as `LastModifiedDate`), the pipeline remembers the last processed record in its "state". During the next execution, it only retrieves data created or modified since that date.

```python
@dlt.resource(primary_key="Id", write_disposition="merge")
def salesforce_accounts(
    last_date=dlt.sources.incremental("LastModifiedDate")
):
    # DLT automatically manages the value of last_date between executions
    yield from get_data_from_sf(since=last_date)
```

---

## Supported Ecosystem

### Sources
DLT can extract data from various sources: REST APIs, SQL, S3, Google Sheets, etc. **Stairway to Salesforce** extends this ecosystem by adding support for the **Salesforce Bulk API v2**.

### Destinations
All standard DLT destinations are supported (Postgres, BigQuery, Snowflake, DuckDB...). Our framework also uses DLT's custom destination interface to allow sending data *to* Salesforce.

---

## Deployment
Since pipelines are simple Python scripts, they integrate everywhere:
* **Local / Cron**: For simple automations.
* **Airflow / Dagster**: Via native operators for robust orchestration.
* **GitHub Actions**: For lightweight and automated deployment directly from your repository.