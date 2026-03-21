"""
Unit tests for Salesforce driver cache manager.

Tests driver caching with TTL support.
"""

import hashlib
from unittest.mock import Mock

import pytest

from stairway_to_salesforce.drivers.salesforce_driver.cache import (
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
        """Test that cache key is SHA-256 hash of secrets path."""
        secrets_path = "salesforce.dev"

        result = get_cache_key(secrets_path)

        # Should be SHA-256 hash
        expected = hashlib.sha256(secrets_path.encode()).hexdigest()
        assert result == expected
        assert len(result) == 64  # SHA-256 hash length

    def test_get_cache_key_different_paths_different_keys(self):
        """Test that different paths generate different keys."""
        key1 = get_cache_key("salesforce.dev")
        key2 = get_cache_key("salesforce.prod")

        assert key1 != key2

    def test_get_cache_key_same_path_same_key(self):
        """Test that same path generates same key (deterministic)."""
        path = "salesforce.dev"

        key1 = get_cache_key(path)
        key2 = get_cache_key(path)

        assert key1 == key2

    def test_get_cache_key_handles_none_path(self):
        """Test with empty or None path behavior."""
        # Empty string should still produce a valid hash
        key = get_cache_key("")
        assert len(key) == 64


class TestDriverCache:
    """Tests for driver_cache management functions."""

    @pytest.fixture(autouse=True)
    def setup_cache(self):
        """Clear cache before each test."""
        clear_cache()
        yield

    def test_add_and_get_driver(self):
        """Test adding a driver to cache and retrieving it."""
        cache_key = "test_key"
        mock_driver = Mock()

        add_driver_to_cache(cache_key, mock_driver)

        assert has_driver_in_cache(cache_key) is True
        assert get_driver_from_cache(cache_key) == mock_driver

    def test_get_non_existent_driver(self):
        """Test getting a driver that isn't in cache."""
        assert get_driver_from_cache("non_existent") is None
        assert has_driver_in_cache("non_existent") is False

    def test_clear_all_cache(self):
        """Test clearing the entire cache."""
        add_driver_to_cache("key1", Mock())
        add_driver_to_cache("key2", Mock())

        clear_cache()

        assert len(driver_cache) == 0

    def test_clear_specific_path(self):
        """Test clearing cache for a specific path."""
        path1 = "salesforce.dev"
        path2 = "salesforce.prod"

        add_driver_to_cache(get_cache_key(path1), Mock())
        add_driver_to_cache(get_cache_key(path2), Mock())

        clear_cache(path1)

        assert has_driver_in_cache(get_cache_key(path1)) is False
        assert has_driver_in_cache(get_cache_key(path2)) is True


class TestCacheManagerScenarios:
    """Scenario-based tests for cache manager."""

    def test_multiple_drivers_caching(self):
        """Test caching multiple drivers for different environments."""
        environments = ["dev", "staging", "prod"]
        drivers = {}

        for env in environments:
            cache_key = get_cache_key(env)
            driver = Mock()
            driver.environment = env
            add_driver_to_cache(cache_key, driver)
            drivers[env] = driver

        # Verify all are cached
        for env in environments:
            cache_key = get_cache_key(env)
            cached_driver = get_driver_from_cache(cache_key)

            assert cached_driver is not None
            assert cached_driver.environment == env

    def test_cache_miss_then_hit_scenario(self):
        """Test typical cache miss followed by cache hit."""
        # IMPORTANT: Ensure cache is clean for this specific path
        path = "salesforce.prod.unique"
        cache_key = get_cache_key(path)

        # Ensure we start from a clean state for this key
        if has_driver_in_cache(cache_key):
            clear_cache(path)

        # First access - cache miss (Should be None)
        result = get_driver_from_cache(cache_key)
        assert result is None

        # Create and cache driver
        mock_driver = Mock()
        add_driver_to_cache(cache_key, mock_driver)

        # Second access - cache hit
        result = get_driver_from_cache(cache_key)
        assert result is mock_driver

    def test_cache_invalidation_scenario(self):
        """Test cache invalidation for credential updates."""
        cache_key = get_cache_key("salesforce.dev")

        # Cache initial driver
        old_driver = Mock()
        old_driver.version = "old"
        add_driver_to_cache(cache_key, old_driver)

        # Simulate credential update - clear cache
        clear_cache("salesforce.dev")

        # Cache new driver
        new_driver = Mock()
        new_driver.version = "new"
        add_driver_to_cache(cache_key, new_driver)

        # Should get new driver
        result = get_driver_from_cache(cache_key)
        assert result == new_driver
        assert result.version == "new"
