"""
Module Sources : Points d'entrée pour l'extraction de données.

Ce package contient les sources DLT permettant de récupérer des données
depuis Salesforce. Il utilise la Factory pour configurer les extractions
via l'API Bulk v2.
"""

from .salesforce_bulk2.source_factory import get_sf_bulk2_source


__version__ = "0.1.0"

__all__ = ["get_sf_bulk2_source"]
