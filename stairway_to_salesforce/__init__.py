# Copyright 2025-2026 Bertrand Leymarios, Geoffrey Bessereau
# and the Stairway to Salesforce Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
DLT Salesforce Advanced - Custom sources, destinations and components for Salesforce.

This package provides production-ready DLT connectors for Salesforce with advanced
features including SOQL injection prevention, comprehensive logging, and error handling.
"""

__version__ = "0.1.0"
__author__ = "Bertrand Leymarios, Geoffrey Bessereau and the Stairway to Salesforce Contributors"

# stairway_to_salesforce/__init__.py
from . import components, destinations, drivers, sources


__all__ = ["sources", "destinations", "components", "drivers"]
