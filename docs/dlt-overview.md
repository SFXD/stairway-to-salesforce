# What is DLT?

[DLT](https://dlthub.com/docs/intro) (Data Load Tool) is the open-source Python library that powers Stairway to Salesforce under the hood. Understanding its core concepts will help you get the most out of this framework.

---

## Overview

DLT is an open-source Python library that loads data from various, often messy data sources into well-structured datasets. It provides lightweight Python interfaces to extract, normalize, transform, and load data — with minimal boilerplate.

```bash
pip install dlt
```

---

## Core Concepts

### Pipeline

A pipeline is the top-level object that connects a source to a destination. It handles execution, state tracking, and schema management.

```python
import dlt

pipeline = dlt.pipeline(
    pipeline_name="my_pipeline",
    destination="duckdb",
    dataset_name="my_dataset"
)
```

In Stairway to Salesforce, the pipeline destination is typically the **Salesforce Bulk2** connector, but any DLT-supported destination works.

### Resource

A resource is a Python generator or function decorated with `@dlt.resource`. It yields records one by one and is the primary unit of data extraction.

```python
@dlt.resource(table_name="accounts")
def get_accounts():
    for record in my_source:
        yield record
```

### Transformer

A transformer is a special resource that receives records from another resource and applies transformations before loading. It is the key building block for the transformation step in Stairway to Salesforce pipelines.

```python
@dlt.transformer(name="transformed_accounts")
def transform_accounts(records: Iterator[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
    for record in records:
        record["Name"] = record["Name"].strip().upper()
        yield record
```

Resources and transformers are chained using the pipe operator:

```python
pipeline.run(source_resource | transformer_resource)
```

### Write Disposition

The write disposition controls how data is written to the destination table. DLT supports three modes:

| Disposition | Behavior |
|---|---|
| `append` | Adds new records to the existing table |
| `replace` | Truncates the table and reloads all data |
| `merge` | Upserts records based on a primary key |

In Stairway to Salesforce, the write disposition is combined with a custom `x-salesforce-operation` hint to drive the Bulk API v2 operation (insert, upsert, delete).

### Schema & Data Types

DLT automatically infers schemas and data types from the data it processes. It handles nested structures by flattening them and tracks schema evolution over pipeline runs, avoiding manual schema maintenance.

### Incremental Loading

DLT supports incremental loading out of the box, allowing pipelines to process only new or updated records since the last run. This is essential for production pipelines on large Salesforce orgs.

```python
@dlt.resource
def get_contacts(
    updated_at = dlt.sources.incremental("SystemModstamp")
):
    ...
```

---

## Supported Sources

DLT can extract from a wide range of sources out of the box:

- REST APIs
- SQL databases (PostgreSQL, MySQL, SQLite, and more)
- Cloud storage (S3, GCS, Azure Blob)
- Python generators and data structures
- [Verified community sources](https://dlthub.com/docs/dlt-ecosystem/verified-sources)

Stairway to Salesforce adds **Salesforce Bulk API v2** as both a source and a destination on top of this ecosystem.

---

## Supported Destinations

DLT supports many popular destinations including Postgres, BigQuery, Snowflake, DuckDB, and Redshift. It also provides a custom destination interface, which is exactly what Stairway to Salesforce uses to implement the Salesforce Bulk2 destination.

---

## Deployment

DLT pipelines run anywhere Python runs. Stairway to Salesforce is compatible with:

- Local execution
- **Apache Airflow** (built-in compatibility)
- Serverless functions (AWS Lambda, Google Cloud Functions)
- Any cloud environment

---

## Further Reading

For a deeper dive into DLT, refer to the official documentation:

- [DLT Introduction](https://dlthub.com/docs/intro)
- [Core Concepts](https://dlthub.com/docs/reference/explainers/how-dlt-works)
- [Incremental Loading](https://dlthub.com/docs/general-usage/incremental-loading)
- [Schema Evolution](https://dlthub.com/docs/general-usage/schema-evolution)
- [Verified Sources](https://dlthub.com/docs/dlt-ecosystem/verified-sources)
- [Destinations](https://dlthub.com/docs/dlt-ecosystem/destinations)
