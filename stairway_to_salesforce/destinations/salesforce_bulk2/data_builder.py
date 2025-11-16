import tempfile
import os
from typing import Iterator
from pathlib import Path
from dlt.common.typing import TDataItems
import pyarrow as pa

def build_data(items: TDataItems) -> str:
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
    
def clean_data(file_path: str):
    if isinstance(file_path, str) and file_path.startswith(tempfile.gettempdir()):
        try:
            os.unlink(file_path)
        except Exception:
            raise ValueError(f"Failed to delete temporary file: {file_path}")
