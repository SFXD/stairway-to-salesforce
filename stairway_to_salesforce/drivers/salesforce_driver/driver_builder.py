import logging
from typing import cast

import dlt
from dlt.sources.helpers.requests import Session
from simple_salesforce import Salesforce

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

# ==========================================
# SECTION 1: INTERNAL HELPERS (PRIVATE)
# ==========================================


def _safe_instantiate(params: dict[str, object]) -> Salesforce:
    """
    Centralized instantiation with error handling for non-JSON responses.
    Uses a targeted type ignore for the external library call.
    """
    try:
        # Mypy requires an ignore here because it cannot verify that
        # dict[str, object] matches the external Salesforce constructor.
        return Salesforce(**params)  # type: ignore[arg-type]
    except Exception as e:
        # Import inside the block to handle specific network response errors
        from requests.exceptions import JSONDecodeError as RequestsJSONDecodeError

        if isinstance(e, RequestsJSONDecodeError):
            logger.error(
                "Salesforce returned a non-JSON response (empty or HTML). "
                "This usually indicates a session timeout or proxy interference."
            )
            raise RuntimeError(
                "Salesforce authentication failed: Invalid server response format."
            ) from e
        logger.error(f"Unexpected error during Salesforce driver instantiation: {e}")
        raise


# ==========================================
# SECTION 2: CREDENTIAL RESOLUTION
# ==========================================


def _resolve_from_dict(cred_dict: dict[str, object]) -> SalesforceDriverAuth:
    """
    Identifies and instantiates the correct Auth spec from a dictionary.
    Explicit mapping ensures strict typing (str | None) without 'Any'.
    """
    if "security_token" in cred_dict:
        return SecurityTokenAuth(
            user_name=cast(str | None, cred_dict.get("user_name")),
            password=cast(str | None, cred_dict.get("password")),
            security_token=cast(str | None, cred_dict.get("security_token")),
        )

    if "organization_id" in cred_dict:
        return OrganizationIdAuth(
            user_name=cast(str | None, cred_dict.get("user_name")),
            password=cast(str | None, cred_dict.get("password")),
            organization_id=cast(str | None, cred_dict.get("organization_id")),
        )

    if "session_id" in cred_dict:
        return InstanceAuth(
            session_id=cast(str | None, cred_dict.get("session_id")),
            instance=cast(str | None, cred_dict.get("instance")),
            instance_url=cast(str | None, cred_dict.get("instance_url")),
        )

    if "privatekey" in cred_dict or "privatekey_file" in cred_dict:
        return JWTAuth(
            user_name=cast(str | None, cred_dict.get("user_name")),
            consumer_key=cast(str | None, cred_dict.get("consumer_key")),
            privatekey_file=cast(str | None, cred_dict.get("privatekey_file")),
            privatekey=cast(str | None, cred_dict.get("privatekey")),
            instance_url=cast(str | None, cred_dict.get("instance_url")),
        )

    if "domain" in cred_dict and "consumer_key" in cred_dict:
        return ConsumerKeySecretDomainAuth(
            consumer_key=cast(str | None, cred_dict.get("consumer_key")),
            consumer_secret=cast(str | None, cred_dict.get("consumer_secret")),
            domain=cast(str | None, cred_dict.get("domain")),
        )

    if "consumer_key" in cred_dict:
        return ConsumerKeySecretAuth(
            user_name=cast(str | None, cred_dict.get("user_name")),
            password=cast(str | None, cred_dict.get("password")),
            consumer_key=cast(str | None, cred_dict.get("consumer_key")),
            consumer_secret=cast(str | None, cred_dict.get("consumer_secret")),
        )

    raise ValueError("Could not determine Salesforce credential type from provided fields.")


def resolve_salesforce_credentials(
    credentials: SalesforceDriverAuth | dict[str, object] | str,
) -> SalesforceDriverAuth:
    """
    Entry point to resolve credentials from various formats.
    """
    if isinstance(
        credentials,
        (
            SecurityTokenAuth,
            OrganizationIdAuth,
            InstanceAuth,
            JWTAuth,
            ConsumerKeySecretAuth,
            ConsumerKeySecretDomainAuth,
        ),
    ):
        return credentials

    if isinstance(credentials, str):
        try:
            cred_dict = cast(dict[str, object], dlt.secrets[credentials])
            return _resolve_from_dict(cred_dict)
        except KeyError as err:
            raise ValueError(f"Failed to load credentials from DLT path: {credentials}") from err

    if isinstance(credentials, dict):
        return _resolve_from_dict(credentials)

    raise TypeError("Credentials must be a SalesforceDriverAuth instance, a dict, or a string.")


# ==========================================
# SECTION 3: DRIVER FACTORY
# ==========================================


def make_salesforce_driver(
    credentials: SalesforceDriverAuth,
    session: Session | None = None,
    config: SalesforceDriverConfiguration | None = None,
) -> Salesforce:
    """
    Main factory function to create a Salesforce driver instance.
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
