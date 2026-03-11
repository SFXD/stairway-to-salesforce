import logging
from dataclasses import dataclass
from typing import List, Optional, Union

from dlt.common.schema import TTableSchema
from tomlkit import key

logger = logging.getLogger(__name__)


@dataclass
class SalesforceDestinationConfig:
    """
    Holds and validates the configuration for a Salesforce Bulk API job
    extracted from the DLT table schema.
    """

    target_object_name: str
    write_disposition: str
    salesforce_operation: str
    primary_key_field: Optional[Union[str, List[str]]]

    @classmethod
    def from_table_schema(
        cls, table_schema: TTableSchema
    ) -> "SalesforceDestinationConfig":
        """
        Factories a config object from DLT metadata with strict validation.
        """
        # 1. Extract basic metadata
        target_name = table_schema.get("name")
        disposition = table_schema.get("write_disposition")
        operation_hint = table_schema.get("x-salesforce-operation")

        if not target_name:
            raise ValueError(
                "Salesforce SObject name must be defined in the table schema."
            )

        # 2. Resolve Primary Key (check top-level then column-level)
        primary_key = table_schema.get("primary_key")
        if not primary_key and "columns" in table_schema:
            primary_key = [
                column_name
                for column_name, column_definition in table_schema["columns"].items()
                if column_definition.get("primary_key") is True
            ]
            # Simplify list to string if only one PK is found
            if primary_key and len(primary_key) == 1:
                primary_key = primary_key[0]

        # 3. Handle Replace Logic
        # In DLT, 'replace' is a specific disposition that overrides hints
        if disposition == "replace":
            if primary_key:
                logger.warning(
                    f"Table '{target_name}' is set to 'replace'. "
                    f"The provided primary key '{primary_key}' will be used for record resolution "
                    "during the deletion phase if applicable."
                )
            resolved_operation = "replace"

        # 4. Handle Append Logic (requires x-salesforce-operation)
        elif disposition == "append":
            if not operation_hint:
                raise ValueError(
                    f"The 'x-salesforce-operation' hint is required for 'append' disposition "
                    f"on table '{target_name}'."
                )
            resolved_operation = operation_hint

        else:
            raise ValueError(f"Unsupported write_disposition: {disposition}")

        # 5. Final validation of operation compatibility
        valid_salesforce_operations = ["insert", "upsert", "delete", "replace"]
        if resolved_operation not in valid_salesforce_operations:
            raise ValueError(
                f"Invalid operation '{resolved_operation}'. "
                f"Supported operations: {valid_salesforce_operations}"
            )

        logger.debug(
            "Destination config received: write=%s, operation=%s, sobject=%s, key=%s",
            disposition,
            resolved_operation,
            target_name,
            key,
        )

        return cls(
            target_object_name=target_name,
            write_disposition=disposition,
            salesforce_operation=resolved_operation,
            primary_key_field=primary_key,
        )
