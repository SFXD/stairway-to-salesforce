from typing import Optional, Union, cast

import json
import dlt

from dlt.sources.helpers.requests import Session
from simple_salesforce import Salesforce
from simple_salesforce.util import Proxies
from simple_salesforce.api import DEFAULT_API_VERSION
from dlt.common.typing import TSecretStrValue
from dlt.common.configuration.specs import (
    CredentialsConfiguration,
    configspec,
    BaseConfiguration,
)
from dlt.common.configuration import with_config
from dlt.common.configuration.exceptions import ConfigurationValueError


@configspec
class SalesforceDriverConfiguration(BaseConfiguration):
    domain: Optional[str] = None
    version: Optional[str] = DEFAULT_API_VERSION
    proxies: Optional[str] = None
    client_id: Optional[str] = None

    def get_proxies(self) -> Optional[Proxies]:
        if self.proxies is None:
            return None
        return cast(Proxies, json.loads(self.proxies))


@configspec
class SalesforceCredentialsBase(CredentialsConfiguration):
    """
    The base version of all the SalesforceCredential classes.
    """


@configspec
class SecurityTokenAuth(SalesforceCredentialsBase):
    """
    This class is used to store 'OAuth 2.0 Username Password Flow Credentials' based on a security token.
    """

    user_name: str = None
    password: TSecretStrValue = None
    security_token: TSecretStrValue = None


@configspec
class OrganizationIdAuth(SalesforceCredentialsBase):
    """
    This class is used to store credentials based on `Trusted IP Ranges` in Salesforce.
    """

    user_name: str = None
    password: TSecretStrValue = None
    organization_id: TSecretStrValue = None


@configspec
class InstanceAuth(SalesforceCredentialsBase):
    """
    This class is used to store credentials for direct session access.
    """

    session_id: str = None
    instance: Optional[TSecretStrValue] = None
    instance_url: Optional[TSecretStrValue] = None

    def on_resolved(self) -> None:
        if not self.instance and not self.instance_url:
            raise ConfigurationValueError(
                "InstanceAuth requires either 'instance' or 'instance_url' to be configured. "
                "Please provide one of these fields."
            )


@configspec
class ConsumerKeySecretAuth(SalesforceCredentialsBase):
    """
    This class is used to store 'OAuth 2.0 Username Password Flow Credentials' based on a connected app.
    """

    user_name: str = None
    password: TSecretStrValue = None
    consumer_key: TSecretStrValue = None
    consumer_secret: TSecretStrValue = None


@configspec
class JWTAuth(SalesforceCredentialsBase):
    """
    This class is used to store 'OAuth 2.0 JWT Bearer Flow Credentials'.
    """

    user_name: str = None
    consumer_key: TSecretStrValue = None
    privatekey_file: Optional[TSecretStrValue] = None
    privatekey: Optional[TSecretStrValue] = None
    instance_url: Optional[TSecretStrValue] = None

    def on_resolved(self) -> None:
        if not self.privatekey_file and not self.privatekey:
            raise ConfigurationValueError(
                "JWTAuth requires either 'privatekey_file' or 'privatekey' to be configured. "
                "Please provide one of these fields."
            )


@configspec
class ConsumerKeySecretDomainAuth(SalesforceCredentialsBase):
    """
    This class is used to store 'OAuth 2.0 Client Credentials Flow'.
    """

    consumer_key: TSecretStrValue = None
    consumer_secret: TSecretStrValue = None
    domain: str = None


SalesforceDriverAuth = Union[
    SecurityTokenAuth,
    OrganizationIdAuth,
    ConsumerKeySecretAuth,
    JWTAuth,
    ConsumerKeySecretDomainAuth,
    InstanceAuth,
]


def resolve_salesforce_credentials(
    credentials: Union[SalesforceDriverAuth, dict, str]
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
    
    Examples:
        >>> # Already a credential object
        >>> creds = SecurityTokenAuth(user_name="...", password="...", security_token="...")
        >>> resolve_salesforce_credentials(creds)  # Returns as-is
        
        >>> # Dictionary
        >>> creds_dict = {"user_name": "...", "password": "...", "security_token": "..."}
        >>> resolve_salesforce_credentials(creds_dict)  # Returns SecurityTokenAuth instance
        
        >>> # DLT secrets path
        >>> resolve_salesforce_credentials("salesforce.production")  # Loads from secrets.toml
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
    if isinstance(credentials, (
        SecurityTokenAuth,
        OrganizationIdAuth,
        InstanceAuth,
        ConsumerKeySecretAuth,
        JWTAuth,
        ConsumerKeySecretDomainAuth
    )):
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
            security_token=credentials.get("security_token")
        )
    
    elif "organization_id" in credentials:
        # Trusted IP Ranges Authentication
        return OrganizationIdAuth(
            user_name=credentials.get("user_name"),
            password=credentials.get("password"),
            organization_id=credentials.get("organization_id")
        )
    
    elif "session_id" in credentials:
        # Direct Session Access
        return InstanceAuth(
            session_id=credentials.get("session_id"),
            instance=credentials.get("instance"),
            instance_url=credentials.get("instance_url")
        )
    
    elif "privatekey" in credentials or "privatekey_file" in credentials:
        # OAuth 2.0 JWT Bearer Flow
        return JWTAuth(
            user_name=credentials.get("user_name"),
            consumer_key=credentials.get("consumer_key"),
            privatekey_file=credentials.get("privatekey_file"),
            privatekey=credentials.get("privatekey"),
            instance_url=credentials.get("instance_url")
        )
    
    elif all(k in credentials for k in ["consumer_key", "consumer_secret", "domain"]):
        # OAuth 2.0 Client Credentials Flow
        return ConsumerKeySecretDomainAuth(
            consumer_key=credentials.get("consumer_key"),
            consumer_secret=credentials.get("consumer_secret"),
            domain=credentials.get("domain")
        )
    
    elif all(k in credentials for k in ["consumer_key", "consumer_secret", "user_name"]):
        # OAuth 2.0 Username-Password Flow with Connected App
        return ConsumerKeySecretAuth(
            user_name=credentials.get("user_name"),
            password=credentials.get("password"),
            consumer_key=credentials.get("consumer_key"),
            consumer_secret=credentials.get("consumer_secret")
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


@with_config(spec=SalesforceDriverConfiguration)
def make_salesforce_driver(
    credentials: SalesforceDriverAuth,
    session: Optional[Session] = None,
    config: SalesforceDriverConfiguration = None,
) -> Salesforce:
    """
    Create a Salesforce client instance with the provided credentials.
    
    This function passes only the necessary arguments to Salesforce depending on the authentication type.
    Note that version, domain, session and proxies are universal kwargs used for all authentication types in
    the Salesforce object.
    
    Args:
        credentials: Salesforce credentials (will be resolved if dict or string)
        session: Optional requests session for connection pooling
        config: Salesforce driver configuration (injected by @with_config)
    
    Returns:
        Configured Salesforce client instance
    
    Raises:
        TypeError: If credentials are invalid or unsupported
    """
    # Resolve credentials to proper type if needed
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
        # NOTE: For this authentication type, domain must be provided as part of the credentials set,
        # we therefore get it from credentials, not config
        return Salesforce(
            version=config.version,
            session=session,
            proxies=config.get_proxies(),
            consumer_key=credentials.consumer_key,
            consumer_secret=credentials.consumer_secret,
            domain=credentials.domain,
        )

    else:
        raise TypeError(
            f"Invalid credentials type: {type(credentials).__name__}. "
            f"Should provide a valid set of Salesforce credentials."
        )