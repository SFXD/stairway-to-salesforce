import dlt
from dlt.common.typing import TDataItems
from dlt.common.schema import TTableSchema
from stairway_to_salesforce.drivers.salesforce_driver import (
    make_salesforce_driver,
    SalesforceDriverAuth
)
from .data_builder import build_data, clean_data

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
    file_path = build_data(items)
    
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

        # Clean up temporary file if created 
        clean_data(file_path)

    except Exception as e:
        raise  RuntimeError(f"Failed to submit Salesforce Bulk API job: {type(e).__name__}")                
    finally:
        # Clean up temporary file if created and any left
        try:
            clean_data(file_path)
        except Exception:
            pass  # Best effort cleanup

