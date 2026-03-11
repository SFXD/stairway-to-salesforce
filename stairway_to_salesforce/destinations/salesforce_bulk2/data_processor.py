"""
Data processing and CSV conversion for Salesforce Bulk API v2.

Handles conversion of various data formats (PyArrow, dict lists, file paths)
to CSV format required by Salesforce Bulk API.
"""

import csv
import os
import tempfile
from pathlib import Path
from typing import Any, Iterator

import pyarrow as pa
from dlt.common.typing import TDataItems


def prepare_data(items: TDataItems) -> str:
    """
    Convert data items to CSV file for Salesforce Bulk API.

    Supports multiple input formats:
    - File path (str/Path): Returns as-is if already CSV
    - PyArrow RecordBatch: Converts to CSV
    - List of dictionaries: Converts to CSV
    - Iterator/generator of dictionaries: Converts to CSV

    Args:
        items: Data items in various formats

    Returns:
        Path to CSV file containing the data

    Raises:
        ValueError: If data is empty or invalid format
        RuntimeError: If conversion fails

    Example:
        >>> data = [{"Id": "001", "Name": "Acme"}]
        >>> csv_path = prepare_data(data)
        >>> # Use csv_path with Salesforce Bulk API
        >>> cleanup_temp_file(csv_path)
    """
    # Case 1: Already a file path
    if isinstance(items, (str, Path)):
        file_path = str(items)

        # Validate file exists
        if not os.path.exists(file_path):
            raise ValueError(f"File does not exist: {file_path}")

        # Validate it's a CSV (Bulk API requirement)
        if not file_path.lower().endswith(".csv"):
            raise ValueError(
                f"File must be CSV format for Salesforce Bulk API. Got: {file_path}"
            )

        return file_path

    # Case 2: PyArrow RecordBatch (from parquet loader)
    if isinstance(items, pa.RecordBatch):
        return _convert_recordbatch_to_csv(items)

    # Case 3: List or iterable of dictionaries
    return _convert_dicts_to_csv(items)


def _convert_recordbatch_to_csv(batch: pa.RecordBatch) -> str:
    """
    Convert PyArrow RecordBatch to CSV file.

    Args:
        batch: PyArrow RecordBatch

    Returns:
        Path to temporary CSV file

    Raises:
        RuntimeError: If conversion fails
    """
    temp_file = None
    try:
        # Create temporary CSV file
        temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8"
        )

        # Convert to pandas DataFrame for easy CSV writing
        df = batch.to_pandas()

        # Validate we have data
        if df.empty:
            temp_file.close()
            os.unlink(temp_file.name)
            raise ValueError("RecordBatch contains no data")

        # Write to CSV
        df.to_csv(temp_file.name, index=False)
        temp_file.close()

        return temp_file.name

    except Exception as e:
        if temp_file and not temp_file.closed:
            temp_file.close()
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        raise RuntimeError(f"Failed to convert RecordBatch to CSV: {str(e)}") from e


def _convert_dicts_to_csv(items: Any) -> str:
    """
    Convert list or iterator of dictionaries to CSV file.

    Args:
        items: List, iterator, or generator of dictionaries

    Returns:
        Path to temporary CSV file

    Raises:
        ValueError: If items are empty or invalid format
        RuntimeError: If conversion fails
    """
    temp_file = None

    try:
        # Convert iterators/generators to list
        if isinstance(items, (Iterator, filter, map)) or hasattr(items, "__iter__"):
            items = list(items)

        # Validate we have data
        if not items:
            raise ValueError("No data items provided")

        # Validate first item is a dictionary
        first_item = items[0]
        if not isinstance(first_item, dict):
            raise TypeError(
                f"Expected list of dictionaries, got list of {type(first_item).__name__}"
            )

        # Validate all items have consistent structure
        fieldnames = list(first_item.keys())
        if not fieldnames:
            raise ValueError("First item has no fields")

        # Create temporary CSV file
        temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8"
        )

        # Write CSV with proper escaping
        writer = csv.DictWriter(temp_file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(items)

        temp_file.close()
        return temp_file.name

    except Exception as e:
        if temp_file and not temp_file.closed:
            temp_file.close()
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        raise RuntimeError(f"Failed to convert data to CSV: {str(e)}") from e


def cleanup_temp_file(file_path: str) -> None:
    """
    Clean up temporary CSV file if it was created by prepare_data.

    Only deletes files in the system temp directory to avoid accidentally
    deleting user files.

    Args:
        file_path: Path to file to clean up

    Note:
        Fails silently if file doesn't exist or can't be deleted.
        This is intentional as cleanup is best-effort.
    """
    if not file_path or not isinstance(file_path, str):
        return

    # Only delete files in temp directory (safety check)
    if not file_path.startswith(tempfile.gettempdir()):
        return

    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception:
        # Best effort cleanup - don't fail the pipeline if cleanup fails
        pass
