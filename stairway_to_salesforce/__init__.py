"""
DLT Salesforce Advanced - Custom sources, destinations and components for Salesforce.

This package provides production-ready DLT connectors for Salesforce with advanced
features including SOQL injection prevention, comprehensive logging, and error handling.
"""

__version__ = "0.1.0"
__author__ = "Bertrand Leymarios"

# stairway_to_salesforce/__init__.py
from . import sources
from . import destinations
from . import components
from . import drivers

__all__ = ['sources', 'destinations', 'components', 'drivers']