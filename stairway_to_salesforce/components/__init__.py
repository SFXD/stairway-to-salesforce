# Copyright 2025-2026 Bertrand Leymarios, Geoffrey Bessereau
# and the Stairway to Salesforce Contributors
# Licensed under the Apache License, Version 2.0 (the "License")

"""
Module Components : Composants logiques et utilitaires métier.

Ce package regroupe les briques réutilisables du framework, notamment
le résolveur de clés Salesforce (SalesforceKeyResolver) pour mapper
les IDs externes, ainsi que les classes de base des pipelines.
"""

from .base_pipeline.base_pipeline import BasePipeline
from .salesforce_key_resolver.resolver import SalesforceKeyResolver
from .salesforce_key_resolver.resolver_factory import get_sf_key_resolver


__version__ = "1.0.0"

__all__ = [
    "BasePipeline",
    "SalesforceKeyResolver",
    "get_sf_key_resolver",
]
