"""Salesforce driver cache with TTL support."""

import hashlib
from typing import Optional
from cachetools import TTLCache
from simple_salesforce import Salesforce

# Global cache: 8 drivers, 1hr TTL (Salesforce default session lifetime)
driver_cache = TTLCache(maxsize=8, ttl=3600)

def get_cache_key(secrets_path: str) -> str:
    """Deterministic cache key from dlt secrets path."""
    return hashlib.md5(secrets_path.encode()).hexdigest()

def has_driver_in_cache(cache_key: str) -> bool:    
    return (cache_key in driver_cache)

def get_driver_from_cache(cache_key: str) -> Salesforce:    
    if cache_key not in driver_cache:
        return None
    
    return driver_cache[cache_key]

def add_driver_to_cache(cache_key: str, driver: Salesforce):
    driver_cache[cache_key] =  driver

def clear_cache(secrets_path: Optional[str] = None):
    if secrets_path:
        cache_key = get_cache_key(secrets_path)
        driver_cache.pop(cache_key, None)
    else:
        driver_cache.clear()
