"""Salesforce credential specification classes only."""

from dlt.common.configuration.exceptions import ConfigurationValueError
from dlt.common.configuration.specs import (
    BaseConfiguration,
    CredentialsConfiguration,
    configspec,
)
from dlt.common.typing import TSecretStrValue
from simple_salesforce.api import DEFAULT_API_VERSION


@configspec
class SalesforceDriverConfiguration(BaseConfiguration):
    domain: str | None = None
    version: str | None = DEFAULT_API_VERSION
    proxies: str | None = None
    client_id: str | None = None

    def get_proxies(self) -> dict | None:
        if self.proxies is None:
            return None
        import json
        from typing import cast

        from simple_salesforce.util import Proxies

        return dict(cast(Proxies, json.loads(self.proxies)))


@configspec
class SalesforceCredentialsBase(CredentialsConfiguration):
    """Base for all Salesforce credential classes."""


# All your @configspec credential classes here...
@configspec
class SecurityTokenAuth(SalesforceCredentialsBase):
    """
    Credentials for **Username-Password Flow with Security Token**.
    
    This is the traditional way to connect without a Connected App, using a 
    combination of user password and a generated security token.

    **Configuration example:**
    ```toml
    [salesforce.dev]
    user_name = "user@example.com"
    password = "your_password"
    security_token = "your_token"
    ```
    """    
    user_name: str | None = None
    password: TSecretStrValue | None = None
    security_token: TSecretStrValue | None = None


@configspec
class OrganizationIdAuth(SalesforceCredentialsBase):
    """
    Credentials for **Trusted IP Ranges Authentication**.
    
    Used when your server's IP is allowlisted in Salesforce, requiring 
    only the Organization ID instead of a security token.

    **Configuration example:**
    ```toml
    [salesforce.dev]
    user_name = "user@example.com"
    password = "your_password"
    organization_id = "00D..."
    ```
    """
    user_name: str | None = None
    password: TSecretStrValue | None = None
    organization_id: TSecretStrValue | None = None


@configspec
class InstanceAuth(SalesforceCredentialsBase):
    """
    Credentials for **Direct Session Access**.
    
    Use this if you already have a valid `session_id` (access token) 
    and want to bypass the authentication flow.

    **Configuration example:**
    ```toml
    [salesforce.dev]
    session_id = "your_access_token"
    instance_url = "[https://yourorg.my.salesforce.com](https://yourorg.my.salesforce.com)"
    ```
    """
    session_id: str | None = None
    instance: TSecretStrValue | None = None
    instance_url: TSecretStrValue | None = None

    def on_resolved(self) -> None:
        if not self.instance and not self.instance_url:
            raise ConfigurationValueError(
                "InstanceAuth requires either 'instance' or 'instance_url' to be configured. "
                "Please provide one of these fields."
            )


@configspec
class ConsumerKeySecretAuth(SalesforceCredentialsBase):
    """
    Credentials for **OAuth 2.0 Username-Password Flow**.
    
    Requires a **Connected App** with `client_id` and `client_secret`. 
    Ideal for legacy integrations that still require user context.

    **Configuration example:**
    ```toml
    [salesforce.dev]
    user_name = "user@example.com"
    password = "your_password"
    consumer_key = "your_client_id"
    consumer_secret = "your_client_secret"
    ```
    """

    user_name: str | None = None
    password: TSecretStrValue | None = None
    consumer_key: TSecretStrValue | None = None
    consumer_secret: TSecretStrValue | None = None


@configspec
class JWTAuth(SalesforceCredentialsBase):
    """
    Credentials for **OAuth 2.0 JWT Bearer Flow**.
    
    The most secure server-to-server flow. It uses a private key to sign 
    a JWT, avoiding the need to store passwords.

    **Configuration example:**
    ```toml
    [salesforce.dev]
    user_name = "user@example.com"
    consumer_key = "your_client_id"
    privatekey_file = "path/to/server.key"
    instance_url = "[https://yourorg.my.salesforce.com](https://yourorg.my.salesforce.com)"
    ```
    """

    user_name: str | None = None
    consumer_key: TSecretStrValue | None = None
    privatekey_file: TSecretStrValue | None = None
    privatekey: TSecretStrValue | None = None
    instance_url: TSecretStrValue | None = None

    def on_resolved(self) -> None:
        if not self.privatekey_file and not self.privatekey:
            raise ConfigurationValueError(
                "JWTAuth requires either 'privatekey_file' or 'privatekey' to be configured. "
                "Please provide one of these fields."
            )


@configspec
class ConsumerKeySecretDomainAuth(SalesforceCredentialsBase):
    """
    Credentials for **OAuth 2.0 Client Credentials Flow** (Recommended).
    
    The modern Salesforce standard for headless integrations. Uses an 
    **External Client App** or Connected App configured for Client Credentials.

    **Configuration example:**
    ```toml
    [salesforce.dev]
    auth_type = "client_credentials" # Used by factory to route here
    consumer_key = "your_client_id"
    consumer_secret = "your_client_secret"
    domain = "yourorg.my" # Optional domain prefix
    ```
    """

    consumer_key: TSecretStrValue | None = None
    consumer_secret: TSecretStrValue | None = None
    domain: str | None = None


SalesforceDriverAuth = (
    SecurityTokenAuth
    | OrganizationIdAuth  # noqa: W503
    | ConsumerKeySecretAuth  # noqa: W503
    | JWTAuth  # noqa: W503
    | ConsumerKeySecretDomainAuth  # noqa: W503
    | InstanceAuth  # noqa: W503
)
