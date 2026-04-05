import logging

from dlt.sources.helpers.requests import Session
from simple_salesforce import Salesforce

from .driver_resolver import resolve_salesforce_credentials
from .specs import (
    ConsumerKeySecretAuth,
    ConsumerKeySecretDomainAuth,
    InstanceAuth,
    JWTAuth,
    OrganizationIdAuth,
    SalesforceDriverAuth,
    SalesforceDriverConfiguration,
    SecurityTokenAuth,
)


logger = logging.getLogger(__name__)


def _safe_instantiate(params: dict[str, object]) -> Salesforce:
    """
    Centralized instantiation with error handling for non-JSON responses.
    """
    try:
        return Salesforce(**params)  # type: ignore[arg-type]
    except Exception as e:
        from requests.exceptions import JSONDecodeError as RequestsJSONDecodeError

        if isinstance(e, RequestsJSONDecodeError):
            logger.error("Salesforce returned a non-JSON response (timeout or proxy issue).")
            raise RuntimeError(
                "Salesforce authentication failed: Invalid server response format."
            ) from e
        logger.error(f"Unexpected error during Salesforce driver instantiation: {e}")
        raise


def make_salesforce_driver(
    credentials: SalesforceDriverAuth | dict[str, object] | str,
    session: Session | None = None,
    config: SalesforceDriverConfiguration | None = None,
) -> Salesforce:
    """
    Technical factory that maps Specs to Salesforce client parameters.
    """
    resolved_config = config if config is not None else SalesforceDriverConfiguration()
    resolved_credentials = resolve_salesforce_credentials(credentials)

    params: dict[str, object] = {
        "version": resolved_config.version,
        "domain": resolved_config.domain,
        "session": session,
        "proxies": resolved_config.get_proxies(),
    }

    if isinstance(resolved_credentials, SecurityTokenAuth):
        params.update(
            {
                "username": resolved_credentials.user_name,
                "password": resolved_credentials.password,
                "security_token": resolved_credentials.security_token,
                "client_id": resolved_config.client_id,
            }
        )
    elif isinstance(resolved_credentials, InstanceAuth):
        params.update(
            {
                "session_id": resolved_credentials.session_id,
                "instance": resolved_credentials.instance,
                "instance_url": resolved_credentials.instance_url,
            }
        )
    elif isinstance(resolved_credentials, OrganizationIdAuth):
        params.update(
            {
                "username": resolved_credentials.user_name,
                "password": resolved_credentials.password,
                "organizationId": resolved_credentials.organization_id,
                "client_id": resolved_config.client_id,
            }
        )
    elif isinstance(resolved_credentials, ConsumerKeySecretAuth):
        params.update(
            {
                "username": resolved_credentials.user_name,
                "password": resolved_credentials.password,
                "consumer_key": resolved_credentials.consumer_key,
                "consumer_secret": resolved_credentials.consumer_secret,
            }
        )
    elif isinstance(resolved_credentials, JWTAuth):
        params.update(
            {
                "username": resolved_credentials.user_name,
                "instance_url": resolved_credentials.instance_url,
                "consumer_key": resolved_credentials.consumer_key,
                "privatekey_file": resolved_credentials.privatekey_file,
                "privatekey": resolved_credentials.privatekey,
            }
        )
    elif isinstance(resolved_credentials, ConsumerKeySecretDomainAuth):
        params.update(
            {
                "consumer_key": resolved_credentials.consumer_key,
                "consumer_secret": resolved_credentials.consumer_secret,
                "domain": resolved_credentials.domain,
            }
        )
    else:
        raise ValueError(f"Unsupported credential type: {type(resolved_credentials)}")

    return _safe_instantiate(params)
