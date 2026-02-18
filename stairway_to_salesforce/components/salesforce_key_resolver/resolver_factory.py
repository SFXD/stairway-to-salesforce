import logging
from typing import Optional
import dlt

from .resolver import SalesforceKeyResolver


# Module-level singleton resolver to maintain state across datasets
_resolver: Optional[SalesforceKeyResolver] = None

def get_salesforce_key_resolver(credentials=dlt.secrets.value ) -> SalesforceKeyResolver:
    """
    Get or create the singleton resolver instance.
    
    Args:
        credentials: Salesforce credentials
        
    Returns:
        SalesforceKeyResolver instance
    """
    global _resolver
    if _resolver is None:
        _resolver = SalesforceKeyResolver(credentials=credentials)
    return _resolver
