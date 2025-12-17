"""
Salesforce Bulk API v2 job execution and error handling.

Handles insert, upsert, delete, and replace operations with proper validation
and error reporting.
"""
import logging
import tempfile
import os
import csv
import io
from typing import Optional, List, Union
import pandas as pd
from simple_salesforce import Salesforce

# Import shared validators
from dlt_salesforce_advanced.utils.salesforce_validators import (
    sanitize_sobject_name,
    sanitize_field_name,
)
# Import logging utilities
from dlt_salesforce_advanced.utils.logger_config import get_rejected_records_path

# Initialize logger
logger = logging.getLogger("dlt")


def execute_job(
    sf_driver: Salesforce,
    target_name: str,
    salesforce_operation: str,
    primary_key: Optional[Union[str, List[str]]],
    file_path: str
) -> None:
    """
    Execute Salesforce Bulk API v2 job with proper error handling.
    """
    logger.info(f"Starting {salesforce_operation} operation on {target_name}")
    
    # Validate and sanitize object name
    target_name = sanitize_sobject_name(target_name)
    logger.debug(f"Validated object name: {target_name}")
        
    # Get Bulk2 client for the object
    try:
        client = getattr(sf_driver.bulk2, target_name)
        logger.debug(f"Bulk2 client obtained for {target_name}")
    except AttributeError:
        logger.error(f"Invalid Salesforce object name: {target_name}")
        raise ValueError(
            f"Invalid Salesforce object name: '{target_name}'. "
            f"Ensure the object exists in your Salesforce org and you have permission to access it."
        )
    
    # Execute operation based on write_disposition
    try:
        if salesforce_operation == "insert":
            _execute_insert(client, target_name, file_path)
        
        elif salesforce_operation == "upsert":
            _execute_upsert(client, target_name, primary_key, file_path)

        elif salesforce_operation == "delete":
            _execute_delete_from_file(client, target_name, primary_key, file_path)

        elif salesforce_operation == "replace":
            _execute_replace(client, target_name, file_path)
        
        else:
            logger.error(f"Unsupported salesforce_operation: {salesforce_operation}")
            # Note: This list of supported dispositions is now strictly controlled by destination.py
            raise ValueError(
                f"Unsupported salesforce_operation '{salesforce_operation}' for table '{target_name}'. "
                f"Supported: 'insert', 'upsert', 'update', 'delete', 'replace'"
            )
        
        logger.info(f"Completed {salesforce_operation} operation on {target_name}")
    
    except Exception as e:
        logger.error(f"Failed to execute {salesforce_operation} operation: {str(e)}")
        raise RuntimeError(
            f"Failed to execute {salesforce_operation} operation on {target_name}: {str(e)}"
        ) from e


def _execute_insert(client, target_name: str, file_path: str) -> None:
    """Execute insert (append) operation."""
    logger.info(f"Inserting records into {target_name} from {file_path}")
    
    results = client.insert(file_path)
    _process_job_results(client, results, target_name, "insert")


def _execute_upsert(
    client,
    target_name: str,
    primary_key: Union[str, List[str]],
    file_path: str
) -> None:
    """Execute upsert (merge) operation."""
    # Extract first key if list
    external_id = primary_key[0] if isinstance(primary_key, list) else primary_key
    
    # Validate field name (no relationship notation for external IDs)
    external_id = sanitize_field_name(external_id, allow_relationship_notation=False)
    
    logger.info(f"Upserting records into {target_name} using external ID: {external_id}")
    
    results = client.upsert(file_path, external_id_field=external_id)
    _process_job_results(client, results, target_name, "upsert")


def _execute_delete_from_file(
    client,
    target_name: str,
    primary_key: Optional[Union[str, List[str]]],
    file_path: str
) -> None:
    """
    Execute delete (merge/delete_rows) operation from a file.
    The file is expected to contain the IDs or External IDs of records to delete.
    """
    logger.info(f"Deleting records from {target_name} via Bulk API V2 file load.")
    
    # Determine the external ID field if provided. Otherwise, Salesforce assumes the 'Id' column.
    external_id_field = None
    if primary_key:
        # For deletion, we pass the External ID field if provided by the DLT primary_key
        external_id_field = primary_key[0] if isinstance(primary_key, list) else primary_key
        external_id_field = sanitize_field_name(external_id_field, allow_relationship_notation=False)
        logger.info(f"Using external ID field '{external_id_field}' for record identification in delete.")
    
    # Execute delete operation
    # The simple-salesforce delete method handles the file path
    results = client.delete(file_path, external_id_field=external_id_field)
    
    # Process results and check for failures
    _process_job_results(client, results, target_name, "delete")
    
    logger.info(f"Delete operation on {target_name} completed.")


def _execute_delete(client, target_name: str, record_ids: List[str]) -> None:
    """Execute delete operation for a list of record IDs (used internally by replace)."""
    if not record_ids:
        logger.info(f"No records to delete from {target_name}")
        return
    
    logger.info(f"Preparing to delete {len(record_ids)} record(s) from {target_name}")
    
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
        
        logger.debug(f"Created temporary delete file: {temp_file.name}")
        
        # Execute delete operation
        results = client.delete(temp_file.name)
        
        # Process results and check for failures
        _process_job_results(client, results, target_name, "delete")
        
        # Check if any deletions failed - this is critical for replace operation
        for result in results:
            num_failed = result.get('numberRecordsFailed', 0)
            if num_failed > 0:
                logger.error(f"Delete operation had {num_failed} failure(s)")
                raise RuntimeError(
                    f"Failed to delete {num_failed} record(s) from {target_name}. "
                    f"Replace operation cannot continue with existing records remaining."
                )
    
    except Exception as e:
        logger.error(f"Delete operation failed: {str(e)}")
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
                logger.debug(f"Cleaned up temporary delete file: {temp_file.name}")
            except Exception:
                pass


def _execute_replace(client, target_name: str, file_path: str) -> None:
    """Execute replace operation: delete all existing records, then insert new ones."""
    logger.warning(f"⚠️  REPLACE operation on {target_name}: This will DELETE all existing records!")
    
    # Step 1: Query all existing record IDs
    logger.info(f"Step 1: Querying existing records from {target_name}")
    try:
        existing_ids = _query_all_record_ids(client, target_name)
    except Exception as e:
        logger.error(f"Replace operation failed during query phase: {str(e)}")
        raise RuntimeError(
            f"Replace operation failed during query phase: {str(e)}"
        ) from e
    
    # Step 2: Delete all existing records (if any)
    if existing_ids:
        logger.info(f"Step 2: Found {len(existing_ids)} existing record(s) to delete")
        try:
            _execute_delete(client, target_name, existing_ids)
        except Exception as e:
            logger.error(f"Replace operation failed during delete phase: {str(e)}")
            raise RuntimeError(
                f"Replace operation failed during delete phase: {str(e)}"
            ) from e
    else:
        logger.info(f"Step 2: No existing records found in {target_name}")
    
    # Step 3: Insert new records
    logger.info(f"Step 3: Inserting new records into {target_name}")
    try:
        _execute_insert(client, target_name, file_path)
    except Exception as e:
        logger.critical(
            f"Replace operation failed during insert phase: {str(e)}. "
            f"WARNING: Existing records were deleted but new records failed to insert!"
        )
        raise RuntimeError(
            f"Replace operation failed during insert phase: {str(e)}. "
            f"WARNING: Existing records were deleted but new records failed to insert!"
        ) from e
    
    logger.info(f"✓ Replace operation on {target_name} completed successfully")


def _query_all_record_ids(client, target_name: str) -> List[str]:
    """Query all record IDs for a Salesforce object using Bulk API v2."""
    logger.debug(f"Querying all record IDs from {target_name}")
    
    try:
        # Build SOQL query to get all IDs
        soql_query = f"SELECT Id FROM {target_name}"

        record_ids = []
        
        # Query returns chunks
        chunk_count = 0
        for chunk in client.query(soql_query):
            chunk_count += 1
            
            if isinstance(chunk, str):
                # CSV response - parse it
                df = pd.read_csv(io.StringIO(chunk))
                if 'Id' in df.columns:
                    ids = df['Id'].tolist()
                    record_ids.extend(ids)
                    logger.debug(f"Chunk {chunk_count}: Retrieved {len(ids)} IDs")
            
            elif isinstance(chunk, list):
                # List of dicts response
                ids = [record['Id'] for record in chunk if 'Id' in record]
                record_ids.extend(ids)
                logger.debug(f"Chunk {chunk_count}: Retrieved {len(ids)} IDs")
        
        logger.info(f"Retrieved {len(record_ids)} total record ID(s) from {target_name}")
        return record_ids
    
    except Exception as e:
        logger.error(f"Failed to query record IDs from {target_name}: {str(e)}")
        raise RuntimeError(
            f"Failed to query existing record IDs from {target_name}: {str(e)}"
        ) from e


def _process_job_results(client, results, target_name: str, operation: str) -> None:
    """Process and report Bulk API job results with rejected records logging."""
    if not results:
        logger.warning(f"No results returned for {operation} on {target_name}")
        return
    
    for result in results:
        job_id = result.get('job_id')
        if not job_id:
            logger.warning(f"{operation.capitalize()} result missing job_id: {result}")
            continue
        
        # Get job statistics
        num_processed = result.get('numberRecordsProcessed', 0)
        num_failed = result.get('numberRecordsFailed', 0)
        num_successful = num_processed - num_failed
        
        logger.info(
            f"Job {job_id}: Processed={num_processed}, Success={num_successful}, Failed={num_failed}"
        )
        
        # Report based on failure status
        if num_failed > 0:
            # Attempt to retrieve and save detailed failure information
            try:
                failed_records = client.get_failed_records(job_id)
                
                if failed_records:
                    logger.warning(
                        f"{operation.capitalize()} job {job_id} on {target_name} "
                        f"completed with {num_failed} failure(s) out of {num_processed} record(s)"
                    )
                    
                    # Save rejected records to CSV file
                    rejected_file = _save_rejected_records(
                        failed_records,
                        target_name,
                        job_id,
                        operation
                    )
                    
                    logger.error(f"Failed records saved to: {rejected_file}")
                    print(f"⚠️  {num_failed} record(s) failed. See rejected records: {rejected_file}")
                else:
                    logger.warning(
                        f"{operation.capitalize()} job {job_id} had {num_failed} failed record(s), "
                        f"but no additional detail could be retrieved"
                    )
                    print(
                        f"⚠️  {operation.capitalize()} job {job_id} on {target_name} "
                        f"had {num_failed} failed record(s) out of {num_processed}, "
                        f"but no additional detail could be retrieved."
                    )
            
            except Exception as e:
                logger.error(f"Failed to retrieve failure details for job {job_id}: {str(e)}")
                print(
                    f"⚠️  {operation.capitalize()} job {job_id} on {target_name} "
                    f"had {num_failed} failed record(s) out of {num_processed}. "
                    f"Error retrieving failure details: {str(e)}"
                )
            
            # Show successful count for partial success
            if num_successful > 0:
                logger.info(f"Successfully processed: {num_successful} record(s)")
                print(f"   ✓ Successfully processed: {num_successful} record(s)")
        
        else:
            # All records processed successfully
            logger.info(
                f"{operation.capitalize()} job {job_id} on {target_name} "
                f"completed successfully with {num_processed} record(s)"
            )
            print(
                f"✓ {operation.capitalize()} job {job_id} on {target_name} "
                f"completed successfully with {num_processed} record(s) processed."
            )


def _save_rejected_records(
    failed_records: str,
    target_name: str,
    job_id: str,
    operation: str
) -> str:
    """
    Save rejected records to a CSV file.
    
    Args:
        failed_records: CSV string with failed records from Salesforce
        target_name: Salesforce object name
        job_id: Salesforce job ID
        operation: Operation type
    
    Returns:
        Path to the saved rejected records file
    """
    rejected_file_path = get_rejected_records_path(target_name, job_id, operation)
    
    try:
        # Write the failed records CSV to file
        with open(rejected_file_path, 'w', encoding='utf-8', newline='') as f:
            f.write(failed_records)
        
        logger.info(f"Saved {len(failed_records.splitlines()) - 1} rejected record(s) to {rejected_file_path}")
        return str(rejected_file_path)
    
    except Exception as e:
        logger.error(f"Failed to save rejected records to file: {str(e)}")
        # Fall back to console output
        print(f"Failed records detail:\n{failed_records}")
        return "console"