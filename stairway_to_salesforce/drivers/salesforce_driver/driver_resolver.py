import logging
from typing import cast

import dlt

from .specs import (
    ConsumerKeySecretAuth,
    ConsumerKeySecretDomainAuth,
    InstanceAuth,
    JWTAuth,
    OrganizationIdAuth,
    SalesforceDriverAuth,
    SecurityTokenAuth,
)


logger = logging.getLogger(__name__)


def _resolve_from_dict(cred_dict: dict[str, object]) -> SalesforceDriverAuth:
    """
    Identifies and instantiates the correct Auth spec from a dictionary.
    Manual mapping ensures strict typing (str | None) without using 'Any'.
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
    Handles DLT secrets lookup and existing spec objects.
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
