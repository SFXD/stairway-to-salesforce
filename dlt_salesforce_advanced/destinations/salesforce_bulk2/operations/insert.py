import logging
from .common import get_bulk_client, process_results

logger = logging.getLogger("dlt")

def exec_insert(sf_driver, target_name: str, file_path: str, **kwargs) -> None:
    """Execute standard insert operation."""
    client, sanitized_name = get_bulk_client(sf_driver, target_name)
    logger.info(f"Inserting records into {sanitized_name} from {file_path}")
    
    results = client.insert(file_path)
    process_results(client, results, sanitized_name, "insert")