"""
DLT Salesforce Advanced - Custom sources, destinations and components for Salesforce.

This package provides production-ready DLT connectors for Salesforce with advanced
features including SOQL injection prevention, comprehensive logging, and error handling.
"""

__version__ = "0.1.0"
__author__ = "Bertrand Leymarios"

# Optional: Expose main components for easier imports
from dlt_salesforce_advanced.drivers.salesforce_driver import (
    make_salesforce_driver,
    resolve_salesforce_credentials,
    SecurityTokenAuth,
    ConsumerKeySecretDomainAuth,
)

__all__ = [
    "make_salesforce_driver",
    "resolve_salesforce_credentials",
    "SecurityTokenAuth",
    "ConsumerKeySecretDomainAuth",   
]