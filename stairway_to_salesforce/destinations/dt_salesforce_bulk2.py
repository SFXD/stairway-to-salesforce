import dlt
from simple_salesforce import Salesforce
from simple_salesforce.bulk import BulkApiError
import time

@dlt.destination(name="salesforce_bulk2")
def salesforce_bulk2_destination(table: str, rows: iter, credentials: dict):
    # Connect to Salesforce using simple-salesforce
    sf = Salesforce(
        username=credentials["username"],
        password=credentials["password"],
        security_token=credentials["security_token"],
        domain=credentials.get("domain", "login")
    )

    # Create Bulk API 2.0 job for the target Salesforce object and operation
    job = sf.bulk.create_job(object_name=table, operation='insert', contentType='JSON')

    # Upload records in batches to the job
    batch_size = 10000  # Bulk 2.0 supports large batch sizes, adjust as needed
    batch = []
    for row in rows:
        batch.append(row)
        if len(batch) == batch_size:
            sf.bulk.post_batch(job, batch)
            batch = []
    if batch:
        sf.bulk.post_batch(job, batch)

    # Close the job to begin processing
    sf.bulk.close_job(job)

    # Poll job status until done
    while True:
        job_status = sf.bulk.get_job_status(job)
        if job_status['state'] in ('JobComplete', 'Failed', 'Aborted'):
            break
        time.sleep(5)  # wait before polling again

    if job_status['state'] != 'JobComplete':
        raise BulkApiError(f"Bulk job failed with state: {job_status['state']}")

    # Optionally, retrieve results for success/failure reporting here

