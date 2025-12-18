import logging
from typing import Union, List
from dlt_salesforce_advanced.utils.salesforce_validators import sanitize_field_name
from .common import get_bulk_client, process_results

logger = logging.getLogger(__name__)

def exec_upsert(sf_driver, target_name: str, file_path: str, primary_key: Union[str, List[str]], **kwargs) -> None:
    """Execute upsert operation using an External ID."""
    client, sanitized_name = get_bulk_client(sf_driver, target_name)
    
    # Extract and sanitize external ID field
    external_id = primary_key[0] if isinstance(primary_key, list) else primary_key
    external_id = sanitize_field_name(external_id, allow_relationship_notation=False)
    
    logger.info("Upserting %s using External ID: %s",sanitized_name,external_id)
    
    results = client.upsert(file_path, external_id_field=external_id)
    process_results(client, results, sanitized_name, "upsert")