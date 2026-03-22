# Examples

This page presents the sample pipelines included in the pipelines folder.

## Sample 1. CSV to Salesforce Upsert (simple)
**Source Code:** [sample01_upsert_account_csv_sf.py](https://github.com/SFXD/stairway-to-salesforce/blob/main/pipelines/sample01_upsert_account_csv_sf.py)

This example shows a simple upsert scenario. It processes a CSV of account and upsert them based on a custom external field "ExternalID__c".

### How it works
1. **Load CSV:** Reads contact data.
2. **Bulk Upsert:** Sends the enriched data to Salesforce via Bulk API v2.

---

## Sample 2. CSV to Salesforce Upsert (with Key Resolver)
**Source Code:** [sample02_upsert_contact_csv_sf.py](https://github.com/SFXD/stairway-to-salesforce/blob/main/pipelines/sample02_upsert_contact_csv_sf.py)

This example shows the power of the SalesforceKeyResolver. It processes a CSV of contacts where the "Account" is identified by an External ID, not a Salesforce ID.

### How it works
1. **Load CSV:** Reads contact data.
2. **Resolve IDs:** The SalesforceKeyResolver queries Salesforce to find the real AccountId matching the External_ID provided in the CSV.
3. **Bulk Upsert:** Sends the enriched data to Salesforce via Bulk API v2.

---

## Sample 3. Mass Delete from Salesforce
**Source Code:** [sample03_delete_contact_csv_sf.py](https://github.com/SFXD/stairway-to-salesforce/blob/main/pipelines/sample03_delete_contact_csv_sf.py)

A specialized pipeline designed to delete records in bulk based on a list of identifiers (like Emails) provided in a CSV file.

- **Note:** The SalesforceKeyResolver is used behind the scenes to find the mandatory Salesforce Id for the delete operation.
- **Safety:** Always test with a small CSV first!

---

## Sample . Full Data Replacement
**Source Code:** [sample04_replace_fixedrecord_csv_sf.py](https://github.com/SFXD/stairway-to-salesforce/blob/main/pipelines/sample04_replace_fixedrecord_csv_sf.py)

Used for "wiping" a specific SObject and replacing its entire content with new data from a source file.

**Warning:** The replace disposition will trigger a delete of all existing records in the target SObject before inserting the new ones.

---

## Sample 5. Salesforce to PostgreSQL Sync
**Source Code:** [sample05_sync_account_sf_to_postgres.py](https://github.com/SFXD/stairway-to-salesforce/blob/main/pipelines/sample05_sync_account_sf_to_postgres.py)

This pipeline performs an incremental synchronization of Salesforce Accounts to a PostgreSQL database.

### Key Features
- **Incremental logic:** Uses LastModifiedDate as a replication key.
- **Merge Strategy:** Upserts records in Postgres based on the Salesforce Id.
- **Field Mapping:** Demonstrates how to rename Salesforce fields (e.g., Owner.Name) to database-friendly columns (e.g., sf_owner).

---

## Running the examples

You can run any example using **uv**. All examples support the standard CLI arguments provided by BasePipeline.

### Basic run

```bash
uv run pipelines/sample_sync_account_sf_to_postgres.py
```

### Specify an environment (Dev/Prod)

```bash
uv run pipelines/sample_sync_account_sf_to_postgres.py --env prod
```

### Pass a specific CSV path

```bash
uv run pipelines/sample_upsert_contact_csv_sf.py "data/my_new_contacts.csv"
```