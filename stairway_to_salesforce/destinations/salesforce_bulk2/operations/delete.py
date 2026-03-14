import logging
import os
import tempfile

import pandas as pd

from .common import get_bulk_client, process_results

logger = logging.getLogger(__name__)


def exec_delete(
    sf_driver,
    target_name: str,
    file_path: str | None,
    primary_key: str | list[str] | None = None,
    key_resolver=None,
    **kwargs,
) -> None:
    """Execute delete operation with optional External ID resolution."""
    client, sanitized_name = get_bulk_client(sf_driver, target_name)

    final_path = file_path
    temp_id_file = None

    # Handle External ID to SFDC ID resolution
    if file_path and key_resolver and not _is_salesforce_id(primary_key):
        logger.info("Resolving External IDs to Salesforce IDs for %s", sanitized_name)

        # 1. Identify the primary key column name
        pk_col = primary_key[0] if isinstance(primary_key, list) else primary_key

        # 2. Extract unique key values from the CSV to minimize API calls
        df_source = pd.read_csv(file_path, usecols=[pk_col])
        key_values = df_source[pk_col].dropna().unique().tolist()

        # 3. Use resolver to fetch missing mappings from Salesforce
        # We pass key_values to trigger a targeted load (REST API) instead of a full load
        success = key_resolver.set_definition(
            sobject=sanitized_name,
            key_field=pk_col,
            full_load=False,
            key_values=key_values,
        )

        if success:
            # 4. Resolve the 'Id' column for every row in the source
            # try_resolve returns the Salesforce ID if found in cache
            df_source["Id"] = df_source[pk_col].apply(
                lambda x: key_resolver.try_resolve(sanitized_name, pk_col, str(x))
            )

            # 5. Salesforce Bulk Delete ONLY accepts 15/18 character Salesforce IDs.
            # We filter for rows where resolution actually returned a valid ID.
            # (Note: try_resolve returns the original value if not found, so we check for change)
            df_to_delete = df_source[df_source["Id"].str.startswith("00", na=False)][["Id"]]

            if not df_to_delete.empty:
                temp_id_file = tempfile.NamedTemporaryFile(
                    mode="w", suffix=".csv", delete=False, newline=""
                )
                df_to_delete.to_csv(temp_id_file.name, index=False)
                final_path = temp_id_file.name
                temp_id_file.close()
                logger.info("Resolved %i records for deletion.", len(df_to_delete))
            else:
                final_path = None
                logger.warning(
                    "None of the provided %s values could be resolved to a Salesforce ID.",
                    pk_col,
                )

    if not final_path:
        logger.warning("No valid records to delete for %s", sanitized_name)
        return

    try:
        logger.info("Executing Bulk Delete on %s", sanitized_name)
        results = client.delete(final_path)
        process_results(client, results, sanitized_name, "delete")
    finally:
        # Cleanup temporary file if one was created
        if temp_id_file and os.path.exists(temp_id_file.name):
            try:
                os.unlink(temp_id_file.name)
            except Exception as e:
                logger.error(f"Could not delete temp file {temp_id_file.name}: {e}")


def _is_salesforce_id(primary_key: str | list[str] | None) -> bool:
    """Check if the primary key is already the Salesforce 'Id' field."""
    if not primary_key:
        return False
    key = primary_key[0] if isinstance(primary_key, list) else primary_key
    return str(key).lower() == "id"
