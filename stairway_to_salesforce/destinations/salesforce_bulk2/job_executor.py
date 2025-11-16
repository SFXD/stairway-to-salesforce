"""
Salesforce Bulk API v2 job execution and error handling.

Handles insert, upsert, delete, and replace operations with proper validation
and error reporting.
"""

import tempfile
import os
import csv
import io
from typing import Optional, List, Union
import pandas as pd
from simple_salesforce import Salesforce

from stairway_to_salesforce.drivers.salesforce_driver import (
    make_salesforce_driver,
    SalesforceDriverAuth,
)
# Import shared validators
from stairway_to_salesforce.utils.salesforce_validators import (
    sanitize_sobject_name,
    sanitize_field_name,
)


def execute_job(
    credentials: SalesforceDriverAuth,
    target_name: str,
    write_disposition: str,
    primary_key: Optional[Union[str, List[str]]],
    file_path: str
) -> None:
    """
    Execute Salesforce Bulk API v2 job with proper error handling.
    
    Args:
        credentials: Salesforce authentication credentials
        target_name: Salesforce object name (e.g., 'Account', 'Contact')
        write_disposition: How to write data ('append', 'merge', 'replace')
        primary_key: Primary key field(s) for merge/replace operations
        file_path: Path to CSV file containing data
    
    Raises:
        ValueError: If inputs are invalid
        RuntimeError: If Salesforce API operation fails
    
    Example:
        >>> execute_job(
        ...     credentials=creds,
        ...     target_name="Account",
        ...     write_disposition="merge",
        ...     primary_key="Id",
        ...     file_path="/tmp/accounts.csv"
        ... )
    """
    # Validate and sanitize object name
    target_name = sanitize_sobject_name(target_name)
    
    # Initialize Salesforce driver
    try:
        driver = make_salesforce_driver(credentials)
    except Exception as e:
        raise RuntimeError(
            f"Failed to initialize Salesforce driver: {str(e)}"
        ) from e
    
    # Get Bulk2 client for the object
    try:
        client = getattr(driver.bulk2, target_name)
    except AttributeError:
        raise ValueError(
            f"Invalid Salesforce object name: '{target_name}'. "
            f"Ensure the object exists in your Salesforce org and you have permission to access it."
        )
    
    # Execute operation based on write_disposition
    try:
        if write_disposition == "append":
            _execute_insert(client, target_name, file_path)
        
        elif write_disposition == "merge":
            _execute_upsert(client, target_name, primary_key, file_path)
        
        elif write_disposition == "replace":
            _execute_replace(driver, client, target_name, file_path)
        
        else:
            raise ValueError(
                f"Unsupported write_disposition '{write_disposition}' for table '{target_name}'. "
                f"Supported: 'append', 'merge', 'replace'"
            )
    
    except Exception as e:
        raise RuntimeError(
            f"Failed to execute {write_disposition} operation on {target_name}: {str(e)}"
        ) from e


def _execute_insert(client, target_name: str, file_path: str) -> None:
    """
    Execute insert (append) operation.
    
    Args:
        client: Bulk2 client for the object
        target_name: Object name
        file_path: CSV file path
    """
    print(f"Inserting records into {target_name}...")
    
    results = client.insert(file_path)
    _process_job_results(client, results, target_name, "insert")


def _execute_upsert(
    client,
    target_name: str,
    primary_key: Union[str, List[str]],
    file_path: str
) -> None:
    """
    Execute upsert (merge) operation.
    
    Args:
        client: Bulk2 client for the object
        target_name: Object name
        primary_key: External ID field(s)
        file_path: CSV file path
    """
    # Extract first key if list
    external_id = primary_key[0] if isinstance(primary_key, list) else primary_key
    
    # Validate field name (no relationship notation for external IDs)
    external_id = sanitize_field_name(external_id, allow_relationship_notation=False)
    
    print(f"Upserting records into {target_name} using external ID: {external_id}...")
    
    results = client.upsert(file_path, external_id_field=external_id)
    _process_job_results(client, results, target_name, "upsert")


def _execute_delete(client, target_name: str, record_ids: List[str]) -> None:
    """
    Execute delete operation for a list of record IDs.
    
    Args:
        client: Bulk2 client for the object
        target_name: Object name
        record_ids: List of Salesforce record IDs to delete
    
    Raises:
        RuntimeError: If delete operation fails
    """
    if not record_ids:
        print(f"No records to delete from {target_name}")
        return
    
    # Create temporary CSV file with IDs to delete
    temp_file = None
    try:
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.csv',
            delete=False,
            newline='',
            encoding='utf-8'
        )
        
        # Write IDs to CSV
        writer = csv.DictWriter(temp_file, fieldnames=['Id'])
        writer.writeheader()
        writer.writerows([{'Id': record_id} for record_id in record_ids])
        temp_file.close()
        
        # Execute delete operation
        print(f"Deleting {len(record_ids)} record(s) from {target_name}...")
        results = client.delete(temp_file.name)
        
        # Process results and check for failures
        _process_job_results(client, results, target_name, "delete")
        
        # Check if any deletions failed - this is critical for replace operation
        for result in results:
            num_failed = result.get('numberRecordsFailed', 0)
            if num_failed > 0:
                raise RuntimeError(
                    f"Failed to delete {num_failed} record(s) from {target_name}. "
                    f"Replace operation cannot continue with existing records remaining."
                )
    
    except Exception as e:
        raise RuntimeError(
            f"Failed to delete records from {target_name}: {str(e)}"
        ) from e
    
    finally:
        # Cleanup temp file
        if temp_file and not temp_file.closed:
            temp_file.close()
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except Exception:
                pass  # Best effort cleanup


def _execute_replace(driver: Salesforce, client, target_name: str, file_path: str) -> None:
    """
    Execute replace operation: delete all existing records, then insert new ones.
    
    This is a destructive operation that will delete ALL records from the
    Salesforce object before inserting new data.
    
    Args:
        driver: Salesforce driver instance
        client: Bulk2 client for the object
        target_name: Object name
        file_path: CSV file path with new data
    
    Raises:
        RuntimeError: If any step of the replace operation fails
    
    Warning:
        This operation is DESTRUCTIVE and will delete all existing records!
    """
    print(f"⚠️  REPLACE operation on {target_name}: This will DELETE all existing records!")
    
    # Step 1: Query all existing record IDs
    try:
        existing_ids = _query_all_record_ids(driver, target_name)
    except Exception as e:
        raise RuntimeError(
            f"Replace operation failed during query phase: {str(e)}"
        ) from e
    
    # Step 2: Delete all existing records (if any)
    if existing_ids:
        print(f"Found {len(existing_ids)} existing record(s) to delete...")
        try:
            _execute_delete(client, target_name, existing_ids)
        except Exception as e:
            raise RuntimeError(
                f"Replace operation failed during delete phase: {str(e)}"
            ) from e
    else:
        print(f"No existing records found in {target_name}")
    
    # Step 3: Insert new records
    print(f"Inserting new records into {target_name}...")
    try:
        _execute_insert(client, target_name, file_path)
    except Exception as e:
        raise RuntimeError(
            f"Replace operation failed during insert phase: {str(e)}. "
            f"WARNING: Existing records were deleted but new records failed to insert!"
        ) from e
    
    print(f"✓ Replace operation on {target_name} completed successfully")


def _query_all_record_ids(driver: Salesforce, target_name: str) -> List[str]:
    """
    Query all record IDs for a Salesforce object using Bulk API v2.
    
    This function is used by the replace operation to identify all existing
    records that need to be deleted before inserting new data.
    
    Args:
        driver: Authenticated Salesforce client
        target_name: Salesforce object name (must be pre-validated)
    
    Returns:
        List of record IDs (Salesforce Id field values)
    
    Raises:
        RuntimeError: If query fails
    
    Example:
        >>> ids = _query_all_record_ids(driver, "Account")
        >>> print(f"Found {len(ids)} existing records")
    """
    try:
        # Build SOQL query to get all IDs
        soql_query = f"SELECT Id FROM {target_name}"
        
        client = getattr(driver.bulk2, target_name)
        record_ids = []
        
        # Query returns chunks
        for chunk in client.query(soql_query):
            if isinstance(chunk, str):
                # CSV response - parse it
                df = pd.read_csv(io.StringIO(chunk))
                if 'Id' in df.columns:
                    record_ids.extend(df['Id'].tolist())
            
            elif isinstance(chunk, list):
                # List of dicts response
                record_ids.extend([record['Id'] for record in chunk if 'Id' in record])
        
        return record_ids
    
    except Exception as e:
        raise RuntimeError(
            f"Failed to query existing record IDs from {target_name}: {str(e)}"
        ) from e


def _process_job_results(client, results, target_name: str, operation: str) -> None:
    """
    Process and report Bulk API job results.
    
    Args:
        client: Bulk2 client for the object
        results: Job results from Salesforce
        target_name: Object name
        operation: Operation type (insert, upsert, delete)
    
    Note:
        Results contain job metadata including:
        - job_id: Unique identifier for the job
        - numberRecordsProcessed: Total records processed
        - numberRecordsFailed: Number of failed records
    """
    if not results:
        print(f"No results returned for {operation} on {target_name}")
        return
    
    for result in results:
        job_id = result.get('job_id')
        if not job_id:
            print(f"⚠️  {operation.capitalize()} result missing job_id: {result}")
            continue
        
        # Get job statistics
        num_processed = result.get('numberRecordsProcessed', 0)
        num_failed = result.get('numberRecordsFailed', 0)
        num_successful = num_processed - num_failed
        
        # Report based on failure status
        if num_failed > 0:
            # Attempt to retrieve detailed failure information
            try:
                failed_records = client.get_failed_records(job_id)
                
                if failed_records:
                    print(
                        f"⚠️  {operation.capitalize()} job {job_id} on {target_name} "
                        f"completed with {num_failed} failure(s) out of {num_processed} record(s):"
                    )
                    print(f"Failed records detail: {failed_records}")
                    
                    # Optionally save failed records to file for debugging
                    # Uncomment if you want to save failed records
                    # failed_file = f"{job_id}_{operation}_failed.csv"
                    # client.get_failed_records(job_id, path=failed_file)
                    # print(f"Failed records saved to: {failed_file}")
                else:
                    print(
                        f"⚠️  {operation.capitalize()} job {job_id} on {target_name} "
                        f"had {num_failed} failed record(s) out of {num_processed}, "
                        f"but no additional detail could be retrieved."
                    )
            
            except Exception as e:
                # Failed to retrieve failure details
                print(
                    f"⚠️  {operation.capitalize()} job {job_id} on {target_name} "
                    f"had {num_failed} failed record(s) out of {num_processed}. "
                    f"Error retrieving failure details: {str(e)}"
                )
            
            # Show successful count for partial success
            if num_successful > 0:
                print(f"   ✓ Successfully processed: {num_successful} record(s)")
        
        else:
            # All records processed successfully
            print(
                f"✓ {operation.capitalize()} job {job_id} on {target_name} "
                f"completed successfully with {num_processed} record(s) processed."
            )