"""Salesforce source helpers"""

import pendulum

from typing import Optional, Iterable, Dict, Set, Any, cast

from simple_salesforce.exceptions import SalesforceMalformedRequest
from simple_salesforce import Salesforce
from dlt.common.typing import TDataItem

from io import StringIO
import csv

from ..settings import IS_PRODUCTION

def get_records(
    sf: Salesforce,
    sobject: str,
    fields: list[str],
    filter: Optional[str] = None,    
    replication_key: Optional[str] = None,
    last_state: Optional[str] = None,
) -> Iterable[TDataItem]:
    """
    Retrieves records from Salesforce for a specified sObject and a specific soql query

    Args:
        sf (Salesforce): An instance of the Salesforce API client.
        sobject (str): The name of the sObject to retrieve records from.
        soql_query (str): The soql query with SELECT <field to retrieve> FROM <same as sobject parameter>  WHERE <filtering criteria>
        last_state (str, optional): The last known state for incremental loading. Defaults to None.
        replication_key (str, optional): The replication key for incremental loading. Defaults to None.

    Yields:
        Dict[TDataItem]: A dictionary representing a record from the Salesforce sObject.
    """
    predicate, order_by, limit = "", "", ""
    
    if filter: 
        predicate += f"{filter}"
    if replication_key is not None:
        if last_state is not None:
            if predicate:
                predicate += ' AND '
            predicate += f" {replication_key} > {last_state}"
        order_by += f" ORDER BY {replication_key} ASC"
    if predicate:
        predicate = f" WHERE {predicate}" 
    if not IS_PRODUCTION:
        limit = " LIMIT 100"        

    soql_query = f"SELECT {', '.join(fields)} FROM {sobject} {predicate} {order_by} {limit}"

    # Try BULK API V2.0 only
    try:
        n_records =  0
        for chunk in getattr(sf.bulk2, sobject).query(soql_query):
            chunk_records =[]
            headers = None
            if isinstance(chunk, str):
                f = StringIO(chunk)
                reader = csv.DictReader(f)
                # For the first chunk, save headers
                if not headers and reader.fieldnames:
                    headers = reader.fieldnames
                for row in reader:
                    chunk_records.append(row)
            elif isinstance(chunk, list):
                # If simple-salesforce returns a list: append directly
                chunk_records.extend(chunk)            
            yield from chunk_records
            n_records += len(chunk_records)
    except SalesforceMalformedRequest as e:
        raise
