import time
import tempfile
import os
from typing import Any, List, Dict, Iterator
from pathlib import Path
import dlt
from dlt.common.typing import TDataItems
from dlt.common.schema import TTableSchema
from stairway_to_salesforce.drivers.salesforce_driver import (
    make_salesforce_driver,
    SalesforceDriverAuth
)
import pyarrow as pa

@dlt.destination(
    name="salesforce_bulk2",
    loader_file_format="parquet",  # Salesforce Bulk API expects CSV/JSON
    batch_size=10000,
    naming_convention="direct"  # Preserve exact table names for Salesforce objects
)
def salesforce_bulk2(
    items: TDataItems,
    table: TTableSchema,
    credentials: SalesforceDriverAuth = dlt.secrets.value
) -> None:
    """
    DLT destination for Salesforce Bulk API v2
    
    Args:
        items: Data items to load (will be file path or iterable)
        table: Table schema with metadata
        credentials: Salesforce authentication credentials
    """
    
    # Validate required hints
    write_disposition = table.get("write_disposition")
    if write_disposition is None:
        raise ValueError(
            f"write_disposition must be specified for table '{table.get('name', 'unknown')}'"
        )
    
    target_name = table.get("name")
    if target_name is None:
        raise ValueError("Table name must be specified for Salesforce destination")    
    
    # Initialize Salesforce driver
    try:
        driver = make_salesforce_driver(credentials)
        client = getattr(driver.bulk2, target_name)
    except AttributeError:
        raise ValueError(
            f"Invalid Salesforce object name: '{target_name}'. "
            f"Ensure the object exists in your Salesforce org."
        )
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Salesforce driver: {type(e).__name__}") from e
    
    # Handle different item types
    file_path = _prepare_data_file(items)
    
    try:
        results = None
        # Create and submit job
        if write_disposition == "append":
            results = client.insert(file_path)
        elif write_disposition == "merge":
            # Validate primary key exists for merge operations
            primary_key = table.get("primary_key")
            if not primary_key:
                raise ValueError(f"Primary key must be specified for merge operations on '{target_name}'")
            results = client.upsert(file_path, external_id_field=primary_key[0] if isinstance(primary_key, list) else primary_key)
        else:
            raise ValueError(
                f"Unsupported write_disposition '{write_disposition}' for table '{target_name}'. "
                f"Only 'append' (insert) and 'merge' (upsert) are supported."
                )
            
        if not results is None:
            for result in results:
                job_id = result['job_id']
                # also available: get_unprocessed_records, get_successful_records
                data = client.get_failed_records(job_id)
                # or save to file
                #client.get_failed_records(job_id, path=f'{job_id}.csv')
                print (f"failed records: {data}") 

    except Exception as e:
        raise  RuntimeError(f"Failed to submit Salesforce Bulk API job: {type(e).__name__}")                
    finally:
        # Clean up temporary file if created
        if isinstance(file_path, str) and file_path.startswith(tempfile.gettempdir()):
            try:
                os.unlink(file_path)
            except Exception:
                pass  # Best effort cleanup

def _prepare_data_file(items: TDataItems) -> str:
    """
    Prepare data for Salesforce Bulk API
    
    Args:
        items: Can be a file path (str), RecordBatch, list of dicts, or iterable
        
    Returns:
        File path to the data file
    """
    # If items is already a file path string
    if isinstance(items, (str, Path)):
        return str(items)
    
    # If items is a PyArrow RecordBatch (from parquet loader)
    if isinstance(items, pa.RecordBatch):
        # Convert to CSV in a temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        try:
            # Convert RecordBatch to pandas for easy CSV writing
            df = items.to_pandas()
            df.to_csv(temp_file.name, index=False)
            return temp_file.name
        except Exception as e:
            os.unlink(temp_file.name)
            raise RuntimeError(f"Failed to convert RecordBatch to CSV: {type(e).__name__}") from e
    
    # If items is a list or iterable of dictionaries
    try:
        import csv
        
        # Convert to list if it's an iterator/generator
        if isinstance(items, (Iterator, filter, map)):
            items = list(items)
        
        # Validate we have data
        if not items:
            raise ValueError("No data items provided")
        
        # Check if it's a list of dictionaries
        if not isinstance(items, list):
            items = list(items)
        
        if not items:
            raise ValueError("Empty data list provided")
        
        # Validate first item is a dictionary
        first_item = items[0]
        if not isinstance(first_item, dict):
            raise TypeError(
                f"Expected list of dictionaries, got list of {type(first_item).__name__}"
            )
        
        # Create temporary CSV file
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.csv',
            delete=False,
            newline='',
            encoding='utf-8'
        )
        
        try:
            # Get field names from first item
            fieldnames = list(first_item.keys())
            
            writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(items)
            temp_file.close()
            
            return temp_file.name
            
        except Exception as e:
            temp_file.close()
            os.unlink(temp_file.name)
            raise RuntimeError(f"Failed to write data to CSV: {type(e).__name__}") from e
            
    except Exception as e:
        raise RuntimeError(
            f"Failed to prepare data file from {type(items).__name__}: {str(e)}"
        ) from e