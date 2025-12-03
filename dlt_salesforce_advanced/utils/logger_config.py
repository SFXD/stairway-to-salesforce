"""
Shared logging configuration for Salesforce sources and destinations.

This module configures DLT's logger for consistent logging across all
Salesforce-related operations.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# DLT provides its own logger
from dlt.common.logger import get_dlt_logger

def get_salesforce_logger(
    name: str,
    log_dir: Optional[str] = None,
    log_level: str = "INFO"
) -> logging.Logger:
    """
    Get a configured logger for Salesforce operations.
    
    DLT automatically configures logging, but this function provides
    additional customization for Salesforce-specific operations.
    
    Args:
        name: Logger name (e.g., 'salesforce_bulk2.source', 'salesforce_bulk2.destination')
        log_dir: Optional directory for log files (defaults to .dlt/logs)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = get_salesforce_logger('salesforce_bulk2.source')
        >>> logger.info("Starting data extraction from Account")
    """
    # Get DLT's logger (uses standard Python logging internally)
    logger = get_dlt_logger(name)
    if logger is None:
        logger = logging.getLogger(name)  # fallback to standard logger
    
    # Set log level
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Add file handler if log_dir specified
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_path / f"{name.replace('.', '_')}_{timestamp}.log"
        
        # File handler with detailed formatting
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # File gets all messages
        
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_file}")
    
    return logger


def get_rejected_records_path(
    target_name: str,
    job_id: str,
    operation: str,
    output_dir: Optional[str] = None
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