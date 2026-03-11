"""
Shared logging configuration for Salesforce sources and destinations.

This module configures DLT's logger for consistent logging across all
Salesforce-related operations.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional


def get_rejected_records_path(
    target_name: str, job_id: str, operation: str, output_dir: Optional[str] = None
) -> Path:
    """
    Generate path for rejected records CSV file.

    Args:
        target_name: Salesforce object name
        job_id: Salesforce job ID
        operation: Operation type (insert, upsert, delete)
        output_dir: Optional directory for rejected records (defaults to .dlt/rejected_records)

    Returns:
        Path object for the rejected records CSV file

    Example:
        >>> path = get_rejected_records_path("Account", "750xx000000XXXX", "insert")
        >>> # Returns: .dlt/rejected_records/Account_insert_750xx000000XXXX_20250118_143022.csv
    """
    if output_dir:
        base_dir = Path(output_dir)
    else:
        base_dir = Path(".dlt") / "rejected_records"

    base_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{target_name}_{operation}_{job_id}_{timestamp}.csv"

    return base_dir / filename
