from typing import cast

from dlt.common.configuration import with_config
from dlt.sources.helpers.requests import Session
from simple_salesforce import Salesforce

from .driver_builder import make_salesforce_driver
from .driver_cache import (
    add_driver_to_cache,
    get_cache_key,
    get_driver_from_cache,
)
from .specs import (
    SalesforceCredentialsBase,
    SalesforceDriverAuth,
    SalesforceDriverConfiguration,
)


@with_config(spec=SalesforceDriverConfiguration)
def get_sf_driver(
    credentials: SalesforceDriverAuth | str,
    session: Session | None = None,
    config: SalesforceDriverConfiguration | None = None,
) -> Salesforce:
    """
    High-level entry point to create or retrieve a cached Salesforce driver.
    """
    resolved_config = config if config is not None else SalesforceDriverConfiguration()

    if isinstance(credentials, str):
        cache_key = get_cache_key(credentials)
        driver = get_driver_from_cache(cache_key)

        if driver is None:
            driver = make_salesforce_driver(credentials, session, resolved_config)
            add_driver_to_cache(cache_key, driver)
        return driver

    if isinstance(credentials, (dict, SalesforceCredentialsBase)):
        return make_salesforce_driver(
            cast(SalesforceDriverAuth, credentials), session, resolved_config
        )

    raise ValueError(
        "Invalid credentials type provided. Expected string, dict, or Salesforce Auth spec."
    )
