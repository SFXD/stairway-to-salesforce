# Architecture

This page details the internal structure of **Stairway to Salesforce** and explains how the framework leverages **dlt** to orchestrate data flows.

---

## Overview

The framework acts as an abstraction layer (wrapper) between data sources and Salesforce APIs, utilizing the **dlt** normalization engine.



---

## Core Components

### 1. BasePipeline
The orchestrator. It inherits capabilities from `dlt.pipeline` and adds:
* **Environment Management**: Automatic loading of secrets based on the `--env` argument.
* **Standardization**: A common interface to launch any type of flow (CSV to SF, SF to SQL, etc.).

### 2. Salesforce Driver
The entry point for authentication. It supports multiple flows (JWT, Password, Client Credentials) and provides a ready-to-use instance for dlt components.

### 3. Sources & Destinations
* **Bulk2 Source**: Uses the Salesforce Bulk API v2 to efficiently extract massive volumes of data.
* **Bulk2 Destination**: A custom dlt destination that translates dlt "write dispositions" into Salesforce operations (Insert, Update, Upsert, Delete).

### 4. SalesforceKeyResolver
A pivotal component that allows handling related data (Lookups/Master-Detail) using **External IDs** instead of technical Salesforce IDs.

---

## Data Flow

Here is the path data takes during a typical import:

1.  **Extraction**: The resource (e.g., a CSV or a SQL query) produces raw records.
2.  **Transformation & Resolution**: 
    * The `KeyResolver` queries Salesforce (if necessary) to convert business identifiers into Salesforce IDs.
    * Transformers clean or remap fields.
3.  **Normalization (dlt)**: dlt flattens the data and verifies correspondence with the destination schema.
4.  **Loading (Bulk API v2)**:
    * The framework batches the data.
    * A Bulk v2 job is created in Salesforce.
    * Data is uploaded, and Salesforce processes the job asynchronously.

---

## State Management

The framework utilizes native **dlt State Management**. This enables:
* **Incrementality**: Storing the last modified date to retrieve only new records in subsequent runs.
* **Error Recovery**: If a job fails, the pipeline knows exactly where it left off.

State is typically stored directly in the destination (e.g., a `_dlt_pipeline_state` table in Postgres) or locally if the destination is Salesforce.