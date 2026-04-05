"""
Unit tests for Salesforce driver cache manager.
Tests driver caching with TTL support.
"""

import hashlib
from unittest.mock import Mock

from stairway_to_salesforce.drivers.salesforce_driver.driver_cache import (
    add_driver_to_cache,
    clear_cache,
    driver_cache,
    get_cache_key,
    get_driver_from_cache,
    has_driver_in_cache,
)


class TestGetCacheKey:
    """Tests for get_cache_key() function."""

    def test_get_cache_key_generates_sha256_hash(self):
        secrets_path = "salesforce.dev"
        result = get_cache_key(secrets_path)
        expected = hashlib.sha256(secrets_path.encode()).hexdigest()
        assert result == expected
        assert len(result) == 64

class TestDriverCacheCore:
    """Tests for core cache operations."""

    def setup_method(self):
        clear_cache()

    def test_add_and_get_driver(self):
        key = "test_key"
        driver = Mock()
        add_driver_to_cache(key, driver)
        assert get_driver_from_cache(key) is driver
        assert has_driver_in_cache(key) is True

    def test_get_non_existent_driver(self):
        assert get_driver_from_cache("non_existent") is None
        assert has_driver_in_cache("non_existent") is False

    def test_clear_specific_entry(self):
        """Tests clear_cache with a specific path."""
        path = "salesforce.test"
        key = get_cache_key(path)
        add_driver_to_cache(key, Mock())

        clear_cache(path)
        assert has_driver_in_cache(key) is False

    def test_clear_full_cache(self):
        """Tests clear_cache without arguments (Covers the 'else' branch)."""
        add_driver_to_cache("key1", Mock())
        add_driver_to_cache("key2", Mock())

        clear_cache()  # Trigger the global clear

        assert len(driver_cache) == 0
