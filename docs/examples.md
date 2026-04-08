# Examples & Tutorials

This page lists the sample pipelines included in the `pipelines/` directory. Each example illustrates a specific capability of the framework.

---

## 🚀 Flagship Pipeline

### [01_get_prospects_from_api.py](https://github.com/SFXD/stairway-to-salesforce/blob/main/pipelines/01_get_prospects_from_api.py)
**Type:** REST API (Gov) ➡️ Salesforce (Bulk API v2)

The recommended starting point. It demonstrates how to fetch JSON data from a public API, transform it, and inject it into Salesforce using an **Upsert** operation.
- **Transformation:** Mapping JSON fields to Salesforce SObject fields.
- **Operation:** Upsert based on a custom SIREN field (`ExternalId__c`).

---

## 📥 Data Ingestion (CSV to Salesforce)

### [10_import_accounts_csv.py](https://github.com/SFXD/stairway-to-salesforce/blob/main/pipelines/10_import_accounts_csv.py)
**Type:** Local File ➡️ Salesforce

A classic bulk import scenario. It reads a CSV file containing company data and updates/creates the corresponding Accounts.
- **Operation:** Bulk Upsert.
- **Prerequisite:** `ExternalId__c` field on the Account object.

### [11_import_contacts_with_lookup.py](https://github.com/SFXD/stairway-to-salesforce/blob/main/pipelines/11_import_contacts_with_lookup.py)
**Type:** Complex Lookup using **SalesforceKeyResolver**

One of the framework's most powerful features. It demonstrates how to import Contacts linked to Accounts using only External IDs (instead of Salesforce 18-char IDs) thanks to the `SalesforceKeyResolver`.
- **Transformation:** Dynamic ID resolution (External ID ➡️ AccountId).

---

## 🛠️ Maintenance & Cleanup

### [12_delete_records_csv.py](https://github.com/SFXD/stairway-to-salesforce/blob/main/pipelines/12_delete_records_csv.py)
**Type:** Bulk Delete

Mass deletes Salesforce records based on a list of IDs or Emails provided in a CSV file.
- **Operation:** Hard Delete / Delete via Bulk API v2.

### [13_reset_custom_table_csv.py](https://github.com/SFXD/stairway-to-salesforce/blob/main/pipelines/13_reset_custom_table_csv.py)
**Type:** Full Table Reset (**Replace**)

Demonstrates the `replace` write disposition: all existing data in the target SObject is deleted and replaced by the new content from the source file.
- **Use Case:** Reference tables, configuration settings.

---

## 📤 Extraction & Sync (Salesforce to ...)

### [20_sync_sf_to_postgres.py](https://github.com/SFXD/stairway-to-salesforce/blob/main/pipelines/20_sync_sf_to_postgres.py)
**Type:** Salesforce ➡️ PostgreSQL

Synchronizes your Salesforce data to a relational database.
- **Strategy:** Incremental (based on `LastModifiedDate`).
- **Destination:** PostgreSQL (utilizing standard DLT connectors).

### **Coming soon** 21_sync_sf_to_csv.py
**Type:** Salesforce ➡️ Local CSV (Extraction)

Extracts Salesforce data and saves it as timestamped CSV files.
- **Use Case:** Local backups, data exports for third-party analysis.

---

## 💡 How to run the examples

All examples are executed via `uv` and support the `--env` argument to switch between your `dev` and `prod` configurations defined in `.dlt/secrets.toml`.

```bash
# Example: Run the account import
uv run pipelines/10_import_accounts_csv.py --env dev
```

## Pipeline Structure

Every sample inherits from BasePipeline and follows the same 5-step logic:

1. Init: Initialize the DLT pipeline with a destination.
2. Source: Define the data source (API, CSV, DB).
3. Transform: Clean and map data (Optional).
4. Destination: Configure "hints" (Target SObject, operation type).
5. Run: Execute the pipeline and display the load report.
