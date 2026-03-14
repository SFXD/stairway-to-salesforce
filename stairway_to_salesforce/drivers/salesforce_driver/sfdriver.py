from typing import cast

import dlt
from dlt.common.configuration import with_config
from dlt.sources.helpers.requests import Session
from simple_salesforce import Salesforce

from .sfdriver_cache_manager import add_driver_to_cache, get_cache_key, get_driver_from_cache
from .sfdriver_factory import make_salesforce_driver
from .sfdriver_specs import (
    SalesforceCredentialsBase,
    SalesforceDriverAuth,
    SalesforceDriverConfiguration,
)


@with_config(spec=SalesforceDriverConfiguration)
def get_salesforce_driver(
    credentials: SalesforceDriverAuth | str,
    session: Session | None = None,
    config: SalesforceDriverConfiguration | None = None,
) -> Salesforce:
    """Create or retrieve cached Salesforce driver."""

    # Ensure config is never None, fall back to defaults
    resolved_config = config if config is not None else SalesforceDriverConfiguration()

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
                raise ValueError(
                    f"Failed to load credentials for {credentials}, " f"exception: {e}"
                )

            # build driver and cache it
            driver = make_salesforce_driver(sf_credential, session, resolved_config)
            add_driver_to_cache(cache_key, driver)
        return driver

    # Credential structure => direct creation without cache
    elif isinstance(credentials, (dict, SalesforceCredentialsBase)):
        auth = cast(SalesforceDriverAuth, credentials)
        return make_salesforce_driver(auth, session, resolved_config)

    else:
        raise ValueError("Error: incorrect credentials passed")
