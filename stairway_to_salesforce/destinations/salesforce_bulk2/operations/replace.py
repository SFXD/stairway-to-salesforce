import io
import logging
import os
import tempfile

import pandas as pd

from stairway_to_salesforce.utils.salesforce_validators import sanitize_sobject_name

from .common import get_bulk_client
from .delete import exec_delete
from .insert import exec_insert

logger = logging.getLogger(__name__)


def exec_replace(sf_driver, target_name: str, file_path: str, **kwargs) -> None:
    """Execute replace: query all IDs, delete them, then insert new file."""
    logger.warning("Starting REPLACE on %s. Existing data will be removed.", target_name)

    # 1. Query Phase: Get all existing IDs to wipe the table
    existing_ids = _query_all_ids(sf_driver, target_name)

    if existing_ids:
        # 2. Delete Phase: Reuse exec_delete with a temporary ID file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmp:
            df = pd.DataFrame(existing_ids, columns=["Id"])
            df.to_csv(tmp.name, index=False)
            tmp_path = tmp.name

        try:
            exec_delete(sf_driver, target_name, file_path=tmp_path, primary_key="Id")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # 3. Insert Phase: Reuse exec_insert for the new data
    exec_insert(sf_driver, target_name, file_path)


def _query_all_ids(sf_driver, target_name: str) -> list[str]:
    """Internal helper to fetch all IDs for the replace operation."""
    target_name = sanitize_sobject_name(target_name)
    client, _ = get_bulk_client(sf_driver, target_name)
    ids = []

    # Bulk 2.0 query returns an iterator of CSV chunks
    # target_name was sanitized against soql injection
    for chunk in client.query(f"SELECT Id FROM {target_name}"):  # nosec B608
        df = pd.read_csv(io.StringIO(chunk))
        if not df.empty:
            ids.extend(df["Id"].tolist())
    return ids
