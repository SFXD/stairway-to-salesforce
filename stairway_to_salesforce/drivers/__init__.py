# Copyright 2025-2026 Bertrand Leymarios, Geoffrey Bessereau
# and the Stairway to Salesforce Contributors
# Licensed under the Apache License, Version 2.0 (the "License")

"""
Module Drivers : Points d'entrée pour les connexions aux systèmes externes.

Ce package regroupe les drivers permettant d'interagir avec différentes APIs.
Chaque sous-dossier (ex: salesforce_driver) gère sa propre logique
d'authentification et de session.
"""

from .salesforce_driver.driver_factory import get_sf_driver


__version__ = "1.0.0"

__all__ = [
    "get_sf_driver",
]
