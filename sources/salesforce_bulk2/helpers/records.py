import pendulum
from typing import Optional, Iterable
from simple_salesforce.exceptions import SalesforceMalformedRequest
from simple_salesforce import Salesforce
from dlt.common.typing import TDataItem

import io
import pandas as pd

from ..settings import IS_PRODUCTION

def _build_soql_query(source_sobject: str, fields: dict[str,str], source_query_filter: Optional[str] = None, source_replication_key: Optional[str] = None,  last_state: Optional[str] = None) -> str:
    predicate, order_by, limit = "", "", ""
    source_fields = list(fields.keys())

    if source_query_filter:
        predicate += f"{source_query_filter}"
    if source_replication_key is not None:
        if last_state is not None:
            if predicate:
                predicate += " AND "
            predicate += f" {source_replication_key} > {last_state}"
        order_by += f" ORDER BY {source_replication_key} ASC"
    if predicate:
        predicate = f" WHERE {predicate}"
    if not IS_PRODUCTION:
        limit = " LIMIT 100"
    return f"SELECT {', '.join(source_fields)} FROM {source_sobject} {predicate} {order_by} {limit}"

def get_records(
    sf: Salesforce,
    source_sobject: str,
    fields: dict[str,str],    
    source_replication_key: Optional[str] = None,
    last_state: Optional[str] = None,
    source_query_filter: Optional[str] = None,
    field_aliases: Optional[dict[str, str]] = None,
) -> Iterable[TDataItem]:

    soql_query = _build_soql_query(source_sobject, fields, source_query_filter, source_replication_key, last_state)    
    print(f"SOQL Query: {soql_query}")

    try:
        for chunk in getattr(sf.bulk2, source_sobject).query(soql_query):
            records = []
            if isinstance(chunk, str):
                f = io.BytesIO(chunk.encode("utf-8"))
                df = pd.read_csv(f)
            elif isinstance(chunk, list):
                df = pd.DataFrame(chunk)
            else:
                df = None

            if df is not None:
                df.rename(columns=fields, inplace=True)
                records = df.to_dict(orient="records")

            if records:
                yield records
    except SalesforceMalformedRequest as e:
        raise
