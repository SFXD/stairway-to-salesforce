"""Source for Salesforce depending on the simple_salesforce python package.

Imported resources are: account, campaign, contact, lead, opportunity, pricebook_2, pricebook_entry, product_2, user and user_role

Salesforce api docs: https://developer.salesforce.com/docs/apis

To get the security token: https://onlinehelp.coveo.com/en/ces/7.0/administrator/getting_the_security_token_for_your_salesforce_account.htm
"""

from dlt.sources import DltResource
from dlt.sources import incremental

from typing import Iterable, Optional

import dlt
from dlt.sources.helpers.requests import Session
from dlt.common.typing import TDataItem
from sqlglot import column

from .helpers.records import get_records
from .helpers.client import SalesforceAuth, make_salesforce_client

@dlt.source(name="salesforce_bulk2")
def salesforce_bulk2_source(
    credentials: SalesforceAuth = dlt.secrets.value,
    session: Optional[Session] = None,
):
    
    """Returns no resources by default. Developers must declare their own."""
    yield from ()  # Empty yield to keep structure valid

def build_resource( target_name: str, target_primary_key: str, 
                    source_sobject: str, fields: dict[str,str], 
                    write_disposition: str, source_replication_key: Optional[str] = None, 
                    source_query_filter: Optional[str] = None, 
                    target_column_types: Optional[list[column]] = None):
    """Factory for DLT resource dynamically wrapping Salesforce client."""
    incremental_cursor = None
    if source_replication_key:
        replication_key = fields[source_replication_key] if (fields and source_replication_key in fields) else source_replication_key
        incremental_cursor = dlt.sources.incremental(replication_key, initial_value=None)

    @dlt.resource(
        name=target_name,
        primary_key=target_primary_key,
        write_disposition=write_disposition,
        columns=target_column_types
    )
    def sf_dynamic_resource(credentials: SalesforceAuth = dlt.secrets.value,session: Optional[Session] = None, incremental_load=incremental_cursor):
        client = make_salesforce_client(credentials, session)
        last_value = incremental_load.last_value if incremental_cursor and replication_key else None
        yield from get_records( sf=client, source_sobject=source_sobject, fields=fields, 
                               source_replication_key= source_replication_key, last_state=last_value, 
                               source_query_filter=source_query_filter )

    return sf_dynamic_resource()
