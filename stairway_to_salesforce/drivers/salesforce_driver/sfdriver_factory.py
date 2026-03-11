from typing import Optional, Union

import dlt
from dlt.sources.helpers.requests import Session
from simple_salesforce import Salesforce

from .sfdriver_specs import (
    ConsumerKeySecretAuth,
    ConsumerKeySecretDomainAuth,
    InstanceAuth,
    JWTAuth,
    OrganizationIdAuth,
    SalesforceDriverAuth,
    SalesforceDriverConfiguration,
    SecurityTokenAuth,
)


def make_salesforce_driver(
    credentials: SalesforceDriverAuth,
    session: Optional[Session] = None,
    config: SalesforceDriverConfiguration = None,
) -> Salesforce:

    credentials = resolve_salesforce_credentials(credentials)

    if isinstance(credentials, SecurityTokenAuth):
        return Salesforce(
            version=config.version,
            domain=config.domain,
            session=session,
            proxies=config.get_proxies(),
            username=credentials.user_name,
            password=credentials.password,
            security_token=credentials.security_token,
            client_id=config.client_id,
        )

    elif isinstance(credentials, InstanceAuth):
        return Salesforce(
            version=config.version,
            domain=config.domain,
            session=session,
            proxies=config.get_proxies(),
            session_id=credentials.session_id,
            instance=credentials.instance,
            instance_url=credentials.instance_url,
        )

    elif isinstance(credentials, OrganizationIdAuth):
        return Salesforce(
            version=config.version,
            domain=config.domain,
            session=session,
            proxies=config.get_proxies(),
            username=credentials.user_name,
            password=credentials.password,
            organizationId=credentials.organization_id,
            client_id=config.client_id,
        )

    elif isinstance(credentials, ConsumerKeySecretAuth):
        return Salesforce(
            version=config.version,
            domain=config.domain,
            session=session,
            proxies=config.get_proxies(),
            username=credentials.user_name,
            password=credentials.password,
            consumer_key=credentials.consumer_key,
            consumer_secret=credentials.consumer_secret,
        )

    elif isinstance(credentials, JWTAuth):
        return Salesforce(
            version=config.version,
            domain=config.domain,
            session=session,
            proxies=config.get_proxies(),
            username=credentials.user_name,
            instance_url=credentials.instance_url,
            consumer_key=credentials.consumer_key,
            privatekey_file=credentials.privatekey_file,
            privatekey=credentials.privatekey,
        )

    elif isinstance(credentials, ConsumerKeySecretDomainAuth):
        # NOTE: For this authentication type,
        # domain must be provided as part of the credentials set,
        # we therefore get it from credentials, not config
        return Salesforce(
            version=config.version,
            session=session,
            proxies=config.get_proxies(),
            consumer_key=credentials.consumer_key,
            consumer_secret=credentials.consumer_secret,
            domain=credentials.domain,
        )


def resolve_salesforce_credentials(  # noqa: C901
    credentials: Union[SalesforceDriverAuth, dict, str],
) -> SalesforceDriverAuth:
    """
    Resolve and validate Salesforce credentials from various input formats.

    This function handles:
    - Already instantiated credential objects (returns as-is)
    - Dictionary credentials (converts to appropriate class)
    - String paths to DLT secrets (loads and converts)

    Args:
        credentials: Credentials in various formats:
            - SalesforceDriverAuth instance: returned as-is
            - dict: converted to appropriate credential class
            - str: loaded from DLT secrets path (e.g., "salesforce.dev")

    Returns:
        Properly typed SalesforceDriverAuth instance

    Raises:
        ValueError: If credentials cannot be resolved or are invalid
        TypeError: If credentials are in an unsupported format
    """
    # If it's a string, load from DLT secrets
    if isinstance(credentials, str):
        try:
            credentials = dlt.secrets[credentials]
        except Exception as e:
            raise ValueError(
                f"Failed to load credentials from DLT secrets path '{credentials}': {str(e)}"
            ) from e

    # If already a proper credential object, return it
    if isinstance(
        credentials,
        (
            SecurityTokenAuth,
            OrganizationIdAuth,
            InstanceAuth,
            ConsumerKeySecretAuth,
            JWTAuth,
            ConsumerKeySecretDomainAuth,
        ),
    ):
        return credentials

    # Convert dict to proper credential class
    if not isinstance(credentials, dict):
        raise TypeError(
            f"Credentials must be a SalesforceDriverAuth instance, dict, or string path. "
            f"Got {type(credentials).__name__}"
        )

    # Determine credential type by checking which fields are present
    # Priority order matches Salesforce authentication specificity

    if "security_token" in credentials:
        # OAuth 2.0 Username-Password Flow with Security Token
        return SecurityTokenAuth(
            user_name=credentials.get("user_name"),
            password=credentials.get("password"),
            security_token=credentials.get("security_token"),
        )

    elif "organization_id" in credentials:
        # Trusted IP Ranges Authentication
        return OrganizationIdAuth(
            user_name=credentials.get("user_name"),
            password=credentials.get("password"),
            organization_id=credentials.get("organization_id"),
        )

    elif "session_id" in credentials:
        # Direct Session Access
        return InstanceAuth(
            session_id=credentials.get("session_id"),
            instance=credentials.get("instance"),
            instance_url=credentials.get("instance_url"),
        )

    elif "privatekey" in credentials or "privatekey_file" in credentials:
        # OAuth 2.0 JWT Bearer Flow
        return JWTAuth(
            user_name=credentials.get("user_name"),
            consumer_key=credentials.get("consumer_key"),
            privatekey_file=credentials.get("privatekey_file"),
            privatekey=credentials.get("privatekey"),
            instance_url=credentials.get("instance_url"),
        )

    elif all(k in credentials for k in ["consumer_key", "consumer_secret", "domain"]):
        # OAuth 2.0 Client Credentials Flow
        return ConsumerKeySecretDomainAuth(
            consumer_key=credentials.get("consumer_key"),
            consumer_secret=credentials.get("consumer_secret"),
            domain=credentials.get("domain"),
        )

    elif all(k in credentials for k in ["consumer_key", "consumer_secret", "user_name"]):
        # OAuth 2.0 Username-Password Flow with Connected App
        return ConsumerKeySecretAuth(
            user_name=credentials.get("user_name"),
            password=credentials.get("password"),
            consumer_key=credentials.get("consumer_key"),
            consumer_secret=credentials.get("consumer_secret"),
        )

    else:
        raise ValueError(
            f"Could not determine Salesforce credential type. "
            f"Available fields: {list(credentials.keys())}. "
            f"Supported credential types require one of:\n"
            f"  - SecurityTokenAuth: user_name, password, security_token\n"
            f"  - OrganizationIdAuth: user_name, password, organization_id\n"
            f"  - InstanceAuth: session_id, (instance OR instance_url)\n"
            f"  - JWTAuth: user_name, consumer_key, (privatekey OR privatekey_file)\n"
            f"  - ConsumerKeySecretDomainAuth: consumer_key, consumer_secret, domain\n"
            f"  - ConsumerKeySecretAuth: user_name, password, consumer_key, consumer_secret"
        )
