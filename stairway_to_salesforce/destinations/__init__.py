"""
Module Destinations : Points d'entrée pour le chargement de données.

Ce package définit les destinations personnalisées pour dlt.
Il inclut la destination Salesforce Bulk v2 capable de gérer les opérations
d'insert, update, upsert et delete de manière atomique.
"""

from .salesforce_bulk2.destination_factory import get_sf_bulk2_destination


__version__ = "0.1.0"

__all__ = [
    "get_sf_bulk2_destination",
]
