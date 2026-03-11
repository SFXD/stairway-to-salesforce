"""Salesforce credential specification classes only."""

from typing import Optional, Union

from dlt.common.configuration.exceptions import ConfigurationValueError
from dlt.common.configuration.specs import BaseConfiguration, CredentialsConfiguration, configspec
from dlt.common.typing import TSecretStrValue
from simple_salesforce.api import DEFAULT_API_VERSION


@configspec
class SalesforceDriverConfiguration(BaseConfiguration):
    domain: Optional[str] = None
    version: Optional[str] = DEFAULT_API_VERSION
    proxies: Optional[str] = None
    client_id: Optional[str] = None

    def get_proxies(self) -> Optional[dict]:
        if self.proxies is None:
            return None
        import json
        from typing import cast

        from simple_salesforce.util import Proxies

        return cast(Proxies, json.loads(self.proxies))


@configspec
class SalesforceCredentialsBase(CredentialsConfiguration):
    """Base for all Salesforce credential classes."""


# All your @configspec credential classes here...
@configspec
class SecurityTokenAuth(SalesforceCredentialsBase):
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
