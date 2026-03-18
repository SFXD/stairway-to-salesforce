import logging

from stairway_to_salesforce.utils.logger_config import get_rejected_records_path
from stairway_to_salesforce.utils.salesforce_validators import sanitize_sobject_name


logger = logging.getLogger(__name__)


def get_bulk_client(sf_driver, target_name: str):
    """Utility to get and validate the Bulk2 client."""
    target_name = sanitize_sobject_name(target_name)
    try:
        return getattr(sf_driver.bulk2, target_name), target_name
    except AttributeError as e:
        logger.error(f"Invalid Salesforce object name: {target_name}")
        raise ValueError(f"Invalid Salesforce object name: '{target_name}'.") from e


def process_results(client, results, target_name: str, operation: str) -> None:
    """Shared logic to handle Bulk API success/failure reporting."""
    if not results:
        logger.warning(f"No results returned for {operation} on {target_name}")
        return

    for result in results:
        job_id = result.get("job_id")
        num_failed = result.get("numberRecordsFailed", 0)

        if num_failed > 0:
            failed_records = client.get_failed_records(job_id)
            rejected_file = _save_rejected_records(failed_records, target_name, job_id, operation)
            logger.error(
                f"Failed records saved to: {rejected_file}, for {operation} on {target_name}"
            )
        else:
            logger.info(f"Job {job_id} succeeded for {operation} on {target_name}")


def _save_rejected_records(
    failed_records: str, target_name: str, job_id: str, operation: str
) -> str:
    """Saves rejected CSV data to a local path."""
    rejected_file_path = get_rejected_records_path(target_name, job_id, operation)
    with open(rejected_file_path, "w", encoding="utf-8", newline="") as f:
        f.write(failed_records)
    return str(rejected_file_path)
