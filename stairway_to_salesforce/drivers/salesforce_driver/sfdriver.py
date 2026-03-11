from typing import Optional, Union, cast

import dlt
from dlt.common.configuration import with_config
from dlt.sources.helpers.requests import Session
from simple_salesforce import Salesforce

from .sfdriver_cache_manager import (add_driver_to_cache, get_cache_key,
                                     get_driver_from_cache)
from .sfdriver_factory import make_salesforce_driver
from .sfdriver_specs import SalesforceDriverAuth, SalesforceDriverConfiguration


@with_config(spec=SalesforceDriverConfiguration)
def get_salesforce_driver(
    credentials: SalesforceDriverAuth | str,
    session: Optional[Session] = None,
    config: SalesforceDriverConfiguration = None,
) -> Salesforce:
    """Create or retrieve cached Salesforce driver."""

    # Credential path => use cache
    if isinstance(credentials, str):
        # Check the cache first
        cache_key = get_cache_key(credentials)
        driver = get_driver_from_cache(cache_key)

        # If not retrieve from cache
        if driver is None:
            # get credential from dlt secret
            try:
                sf_credential = dlt.secrets[f"{credentials}"]
            except KeyError as e:
                raise ValueError(f"Failed to load credentials for {credentials}")

            # build driver and cache it
            driver = make_salesforce_driver(sf_credential, session, config)
            add_driver_to_cache(cache_key, driver)
        return driver

    # Credential structure => direct creation without cache
    elif isinstance(credentials, SalesforceDriverAuth):
        return make_salesforce_driver(credentials, session, config)
    else:
        raise ValueError(f"Error: incorrect credentials passed")
