"""
Cache management for Salesforce lookup mappings.
"""

from typing import Dict, Optional, Set

import pandas as pd


class CacheManager:
    """
    Manages in-memory cache for Salesforce ID mappings.

    The cache stores DataFrames mapping external keys to Salesforce IDs,
    organized by sobject and key field.
    """

    def __init__(self):
        """Initialize empty cache."""
        self._cache: Dict[str, pd.DataFrame] = {}

    def get_cache_key(self, sobject: str, key_field: str) -> str:
        """
        Generate cache key from sobject and field.

        Args:
            sobject: Salesforce object name
            key_field: External key field name

        Returns:
            Cache key string
        """
        return f"{sobject}:{key_field}"

    def has_cache(self, sobject: str, key_field: str) -> bool:
        """
        Check if cache exists for the given mapping.

        Args:
            sobject: Salesforce object name
            key_field: External key field name

        Returns:
            True if cache exists, False otherwise
        """
        cache_key = self.get_cache_key(sobject, key_field)
        return cache_key in self._cache

    def get_cache(self, sobject: str, key_field: str) -> pd.DataFrame:
        """
        Get cached DataFrame.

        Args:
            sobject: Salesforce object name
            key_field: External key field name

        Returns:
            Cached DataFrame (may be empty)

        Raises:
            KeyError: If cache doesn't exist
        """
        cache_key = self.get_cache_key(sobject, key_field)
        if cache_key not in self._cache:
            raise KeyError(f"Cache not found for {cache_key}")
        return self._cache[cache_key]

    def initialize_cache(self, sobject: str, key_field: str) -> None:
        """
        Initialize empty cache entry.

        Args:
            sobject: Salesforce object name
            key_field: External key field name
        """
        cache_key = self.get_cache_key(sobject, key_field)
        if cache_key not in self._cache:
            self._cache[cache_key] = pd.DataFrame()

    def update_cache(self, sobject: str, key_field: str, df_new: pd.DataFrame) -> int:
        """
        Add new data to cache and deduplicate.

        Args:
            sobject: Salesforce object name
            key_field: External key field name
            df_new: New DataFrame to add to cache

        Returns:
            Total number of records in cache after update
        """
        cache_key = self.get_cache_key(sobject, key_field)

        # Initialize cache if it doesn't exist
        if cache_key not in self._cache:
            self.initialize_cache(sobject, key_field)

        # Get existing cache
        df_existing = self._cache[cache_key]

        if df_new is None or df_new.empty:
            return len(df_existing)

        # Merge and deduplicate
        df_merged = pd.concat([df_existing, df_new], ignore_index=True)
        df_merged = df_merged.drop_duplicates(subset=[key_field], keep="last")

        # Update cache
        self._cache[cache_key] = df_merged

        return len(df_merged)

    def find_missing_keys(
        self, sobject: str, key_field: str, requested_keys: Set[str]
    ) -> Set[str]:
        """
        Find keys not in cache.

        Args:
            sobject: Salesforce object name
            key_field: External key field name
            requested_keys: Set of keys to check

        Returns:
            Set of keys not found in cache
        """
        cache_key = self.get_cache_key(sobject, key_field)

        if cache_key not in self._cache:
            return requested_keys

        df = self._cache[cache_key]

        if df.empty or key_field not in df.columns:
            return requested_keys

        cached_keys = set(df[key_field].values)
        missing_keys = requested_keys - cached_keys

        return missing_keys

    def resolve_single(
        self, sobject: str, key_field: str, external_value: str
    ) -> Optional[str]:
        """
        Resolve single external ID to Salesforce ID.

        Args:
            sobject: Salesforce object name
            key_field: External key field name
            external_value: External value to resolve

        Returns:
            Salesforce ID if found, None otherwise
        """
        cache_key = self.get_cache_key(sobject, key_field)
        if cache_key not in self._cache:
            return None

        df = self._cache[cache_key]
        if df.empty:
            return None

        # Look up the value
        result = df.loc[df[key_field] == external_value, "Id"]

        if len(result) == 0:
            return None
        if len(result) > 1:
            raise ValueError(f"Multiple IDs found for {cache_key}='{external_value}'.")

        return result.iloc[0]

    def clear(
        self, sobject: Optional[str] = None, key_field: Optional[str] = None
    ) -> None:
        """
        Clear cache entries.

        Args:
            sobject: If specified, only clear this object's caches
            key_field: If specified with sobject, clear only this specific mapping
        """
        if sobject and key_field:
            cache_key = self.get_cache_key(sobject, key_field)
            if cache_key in self._cache:
                del self._cache[cache_key]
        elif sobject:
            keys_to_delete = [
                k for k in self._cache.keys() if k.startswith(f"{sobject}:")
            ]
            for key in keys_to_delete:
                del self._cache[key]
        else:
            count = len(self._cache)
            self._cache.clear()
