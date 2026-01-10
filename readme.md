
Description

## Installation

# run scripts/download_tzdata.py   to download tzdata in the folder "Downloads" of your user.  (Requirement for pyArrow conversion)
uv sync
uv add <package name>
uv add --upgrade <package name>

# Functionalities
- Salesforce Bulk2 as source
- Salesforce Bulk2 as destination with the following capacities
    - insert :  write_disposition = "append"  / x-salesforce-operation = "insert"
    - upsert :  write_disposition = "append"  / x-salesforce-operation = "upsert" / primary_key = "<required>"
    - delete :  write_disposition = "append"  / x-salesforce-operation = "delete" / primary_key = "<required>"
        for an optimized pipeline, the primary_key should Id, as Salesforce Bulk2 does not support deletion on external Id
        if the primary key is not "Id", a query will be performed to convert the external id into a Salesforce Id. 
    - replace : write_disposition = "replace"
        the entiere sobject records will deleted ( Query + delete) and the given data will be inserted.
        To avoid if the source system can transmit incremental update, as it's consuming additional resources (especially with a large data volume) and preventing any historic in Salesforce
- SalesforceKeyResolver as component
    - resolve an External Key as a Salesforce Id -  useful for lookup
- Base pipeline as component


## Usage
#  Start postgres -  (cmd as administrator)
net start postgresql-x64-18
#  Allow vscode command
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
& .venv\scripts\activate 
 
# Launch test pipelines
uv run pipelines\sample_delete_contact_to_sf.py
uv run pipelines\sample_replace_fixedrecord_csv_to_sf.py
uv run pipelines\sample_sync_account_sf_to_postgres.py
uv run pipelines\sample_upsert_contact_csv_sf.py

# Run with coverage
uv run --with pytest pytest
uv run --with pytest pytest --cov=dlt_salesforce_advanced --cov-report=html
uv run --with pytest pytest tests/unit/ --cov=dlt_salesforce_advanced --cov-report=term

# View coverage
uv run --with pytest pytest start htmlcov/index.html
