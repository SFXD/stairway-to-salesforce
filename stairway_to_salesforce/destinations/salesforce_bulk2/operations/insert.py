import logging

from .common import get_bulk_client, process_results


logger = logging.getLogger(__name__)


def exec_insert(sf_driver, target_name: str, file_path: str, **kwargs) -> None:
    client, sanitized_name = get_bulk_client(sf_driver, target_name)
    logger.info("Inserting records into %s from %s", sanitized_name, file_path)
    results = client.insert(file_path)
    process_results(client, results, sanitized_name, "insert")
