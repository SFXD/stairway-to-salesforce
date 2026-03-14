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
    session: Session | None = None,
    config: SalesforceDriverConfiguration | None = None,
) -> Salesforce:

    # Consistency on config ( default if none )
    resolved_config = config if config is not None else SalesforceDriverConfiguration()

    # Consistency on credentials
    resolved_credentials = resolve_salesforce_credentials(credentials)

    if isinstance(resolved_credentials, SecurityTokenAuth):
        return Salesforce(
            version=resolved_config.version,
            domain=resolved_config.domain,
            session=session,
            proxies=resolved_config.get_proxies(),
            username=resolved_credentials.user_name,
            password=resolved_credentials.password,
            security_token=resolved_credentials.security_token,
            client_id=resolved_config.client_id,
        )

    elif isinstance(resolved_credentials, InstanceAuth):
        return Salesforce(
            version=resolved_config.version,
            domain=resolved_config.domain,
            session=session,
            proxies=resolved_config.get_proxies(),
            session_id=resolved_credentials.session_id,
            instance=resolved_credentials.instance,
            instance_url=resolved_credentials.instance_url,
        )

    elif isinstance(resolved_credentials, OrganizationIdAuth):
        return Salesforce(
            version=resolved_config.version,
            domain=resolved_config.domain,
            session=session,
            proxies=resolved_config.get_proxies(),
            username=resolved_credentials.user_name,
            password=resolved_credentials.password,
            organizationId=resolved_credentials.organization_id,
            client_id=resolved_config.client_id,
        )

    elif isinstance(resolved_credentials, ConsumerKeySecretAuth):
        return Salesforce(
            version=resolved_config.version,
            domain=resolved_config.domain,
            session=session,
            proxies=resolved_config.get_proxies(),
            username=resolved_credentials.user_name,
            password=resolved_credentials.password,
            consumer_key=resolved_credentials.consumer_key,
            consumer_secret=resolved_credentials.consumer_secret,
        )

    elif isinstance(resolved_credentials, JWTAuth):
        return Salesforce(
            version=resolved_config.version,
            domain=resolved_config.domain,
            session=session,
            proxies=resolved_config.get_proxies(),
            username=resolved_credentials.user_name,
            instance_url=resolved_credentials.instance_url,
            consumer_key=resolved_credentials.consumer_key,
            privatekey_file=resolved_credentials.privatekey_file,
            privatekey=resolved_credentials.privatekey,
        )

    elif isinstance(resolved_credentials, ConsumerKeySecretDomainAuth):
        # NOTE: For this authentication type,
        # domain must be provided as part of the credentials set,
        # we therefore get it from credentials, not config
        return Salesforce(
            version=resolved_config.version,
            session=session,
            proxies=resolved_config.get_proxies(),
            consumer_key=resolved_credentials.consumer_key,
            consumer_secret=resolved_credentials.consumer_secret,
            domain=resolved_credentials.domain,
        )


def resolve_salesforce_credentials(  # noqa: C901
    credentials: SalesforceDriverAuth | dict | str,
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
            "Could not determine Salesforce credential type. "
            f"Available fields: {list(credentials.keys())}. "
            "Supported credential types require one of:\n"
            "  - SecurityTokenAuth: user_name, password, security_token\n"
            "  - OrganizationIdAuth: user_name, password, organization_id\n"
            "  - InstanceAuth: session_id, (instance OR instance_url)\n"
            "  - JWTAuth: user_name, consumer_key, (privatekey OR privatekey_file)\n"
            "  - ConsumerKeySecretDomainAuth: consumer_key, consumer_secret, domain\n"
            "  - ConsumerKeySecretAuth: user_name, password, consumer_key, consumer_secret"
        )
