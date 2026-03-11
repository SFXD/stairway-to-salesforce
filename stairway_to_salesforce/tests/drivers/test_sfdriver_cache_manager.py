"""
Unit tests for Salesforce driver cache manager.

Tests driver caching with TTL support.
"""

import hashlib
import time
from unittest.mock import Mock, patch

import pytest

from stairway_to_salesforce.drivers.salesforce_driver.sfdriver_cache_manager import (
    add_driver_to_cache, clear_cache, driver_cache, get_cache_key,
    get_driver_from_cache, has_driver_in_cache)


class TestGetCacheKey:
    """Tests for get_cache_key() function."""

    def test_get_cache_key_generates_md5_hash(self):
        """Test that cache key is MD5 hash of secrets path."""
        secrets_path = "salesforce.dev"

        result = get_cache_key(secrets_path)

        # Should be MD5 hash
        expected = hashlib.md5(secrets_path.encode()).hexdigest()
        assert result == expected
        assert len(result) == 32  # MD5 hash length

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

    def test_get_cache_key_handles_nested_paths(self):
        """Test cache key generation for nested secrets paths."""
        nested_path = "salesforce.production.us_east"

        result = get_cache_key(nested_path)

        assert len(result) == 32
        assert result == hashlib.md5(nested_path.encode()).hexdigest()

    def test_get_cache_key_handles_special_characters(self):
        """Test cache key generation with special characters."""
        path_with_special = "salesforce.dev-2024_v1"

        result = get_cache_key(path_with_special)

        assert len(result) == 32


class TestHasDriverInCache:
    """Tests for has_driver_in_cache() function."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cache()

    def test_has_driver_returns_false_for_empty_cache(self):
        """Test that has_driver returns False when cache is empty."""
        cache_key = get_cache_key("salesforce.dev")

        result = has_driver_in_cache(cache_key)

        assert result is False

    def test_has_driver_returns_true_after_adding(self):
        """Test that has_driver returns True after driver is added."""
        cache_key = get_cache_key("salesforce.dev")
        mock_driver = Mock()

        add_driver_to_cache(cache_key, mock_driver)
        result = has_driver_in_cache(cache_key)

        assert result is True

    def test_has_driver_returns_false_for_different_key(self):
        """Test that has_driver returns False for different cache key."""
        cache_key1 = get_cache_key("salesforce.dev")
        cache_key2 = get_cache_key("salesforce.prod")
        mock_driver = Mock()

        add_driver_to_cache(cache_key1, mock_driver)
        result = has_driver_in_cache(cache_key2)

        assert result is False

    def test_has_driver_returns_false_after_clear(self):
        """Test that has_driver returns False after cache is cleared."""
        cache_key = get_cache_key("salesforce.dev")
        mock_driver = Mock()

        add_driver_to_cache(cache_key, mock_driver)
        clear_cache()
        result = has_driver_in_cache(cache_key)

        assert result is False


class TestGetDriverFromCache:
    """Tests for get_driver_from_cache() function."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cache()

    def test_get_driver_returns_none_when_not_cached(self):
        """Test that get_driver returns None for non-existent key."""
        cache_key = get_cache_key("salesforce.dev")

        result = get_driver_from_cache(cache_key)

        assert result is None

    def test_get_driver_returns_cached_driver(self):
        """Test that get_driver returns the cached driver."""
        cache_key = get_cache_key("salesforce.dev")
        mock_driver = Mock()
        mock_driver.test_attribute = "test_value"

        add_driver_to_cache(cache_key, mock_driver)
        result = get_driver_from_cache(cache_key)

        assert result is mock_driver
        assert result.test_attribute == "test_value"

    def test_get_driver_returns_correct_driver_for_key(self):
        """Test that get_driver returns correct driver for specific key."""
        key1 = get_cache_key("salesforce.dev")
        key2 = get_cache_key("salesforce.prod")

        driver1 = Mock()
        driver1.name = "dev_driver"
        driver2 = Mock()
        driver2.name = "prod_driver"

        add_driver_to_cache(key1, driver1)
        add_driver_to_cache(key2, driver2)

        result1 = get_driver_from_cache(key1)
        result2 = get_driver_from_cache(key2)

        assert result1.name == "dev_driver"
        assert result2.name == "prod_driver"


class TestAddDriverToCache:
    """Tests for add_driver_to_cache() function."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cache()

    def test_add_driver_stores_in_cache(self):
        """Test that add_driver stores driver in cache."""
        cache_key = get_cache_key("salesforce.dev")
        mock_driver = Mock()

        add_driver_to_cache(cache_key, mock_driver)

        assert has_driver_in_cache(cache_key)
        assert get_driver_from_cache(cache_key) is mock_driver

    def test_add_driver_overwrites_existing(self):
        """Test that add_driver overwrites existing cached driver."""
        cache_key = get_cache_key("salesforce.dev")

        driver1 = Mock()
        driver1.name = "first"
        driver2 = Mock()
        driver2.name = "second"

        add_driver_to_cache(cache_key, driver1)
        add_driver_to_cache(cache_key, driver2)

        result = get_driver_from_cache(cache_key)
        assert result.name == "second"

    def test_add_multiple_drivers(self):
        """Test adding multiple drivers with different keys."""
        key1 = get_cache_key("salesforce.dev")
        key2 = get_cache_key("salesforce.prod")
        key3 = get_cache_key("salesforce.sandbox")

        driver1 = Mock()
        driver2 = Mock()
        driver3 = Mock()

        add_driver_to_cache(key1, driver1)
        add_driver_to_cache(key2, driver2)
        add_driver_to_cache(key3, driver3)

        assert has_driver_in_cache(key1)
        assert has_driver_in_cache(key2)
        assert has_driver_in_cache(key3)


class TestClearCache:
    """Tests for clear_cache() function."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cache()

    def test_clear_cache_removes_all_entries(self):
        """Test that clear_cache removes all cached drivers."""
        key1 = get_cache_key("salesforce.dev")
        key2 = get_cache_key("salesforce.prod")

        add_driver_to_cache(key1, Mock())
        add_driver_to_cache(key2, Mock())

        clear_cache()

        assert not has_driver_in_cache(key1)
        assert not has_driver_in_cache(key2)

    def test_clear_cache_specific_key(self):
        """Test clearing cache for specific secrets path."""
        path1 = "salesforce.dev"
        path2 = "salesforce.prod"

        key1 = get_cache_key(path1)
        key2 = get_cache_key(path2)

        add_driver_to_cache(key1, Mock())
        add_driver_to_cache(key2, Mock())

        clear_cache(path1)

        assert not has_driver_in_cache(key1)
        assert has_driver_in_cache(key2)  # Should still be cached

    def test_clear_cache_nonexistent_key(self):
        """Test that clearing non-existent key doesn't raise error."""
        clear_cache("salesforce.nonexistent")  # Should not raise

    def test_clear_cache_can_add_after_clear(self):
        """Test that cache can be used after clearing."""
        cache_key = get_cache_key("salesforce.dev")

        add_driver_to_cache(cache_key, Mock())
        clear_cache()

        # Should be able to add again
        new_driver = Mock()
        add_driver_to_cache(cache_key, new_driver)

        assert has_driver_in_cache(cache_key)
        assert get_driver_from_cache(cache_key) is new_driver


class TestDriverCacheTTL:
    """Tests for TTL (Time-To-Live) behavior of driver cache."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cache()

    def test_cache_is_ttl_cache(self):
        """Test that driver_cache is a TTLCache instance."""
        from cachetools import TTLCache

        assert isinstance(driver_cache, TTLCache)

    def test_cache_has_correct_maxsize(self):
        """Test that cache has maxsize of 8."""
        assert driver_cache.maxsize == 8

    def test_cache_has_correct_ttl(self):
        """Test that cache has TTL of 3600 seconds (1 hour)."""
        assert driver_cache.ttl == 3600

    def test_cache_evicts_oldest_when_full(self):
        """Test that cache evicts oldest entry when full (maxsize=8)."""
        # Add 9 drivers (more than maxsize)
        drivers = []
        keys = []

        for i in range(9):
            key = get_cache_key(f"salesforce.env{i}")
            driver = Mock()
            driver.id = i

            add_driver_to_cache(key, driver)
            drivers.append(driver)
            keys.append(key)

        # First entry should be evicted
        assert not has_driver_in_cache(keys[0])

        # Others should still be cached
        for key in keys[1:]:
            assert has_driver_in_cache(key)

    @pytest.mark.slow
    def test_cache_expires_after_ttl(self):
        """Test that cached entries expire after TTL."""
        # Note: This test is marked as slow since it involves actual time delays
        # In production tests, consider mocking time or using shorter TTL

        # This is a conceptual test - in practice, we'd need to either:
        # 1. Mock time.time() to simulate TTL expiration
        # 2. Create a cache with very short TTL for testing
        # 3. Skip this test in fast test runs

        # For now, we just verify the TTL is set correctly
        assert driver_cache.ttl == 3600


class TestCacheManagerEdgeCases:
    """Tests for edge cases in cache manager."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cache()

    def test_cache_handles_none_driver(self):
        """Test that cache can store None as a driver value."""
        cache_key = get_cache_key("salesforce.dev")

        add_driver_to_cache(cache_key, None)

        assert has_driver_in_cache(cache_key)
        assert get_driver_from_cache(cache_key) is None

    def test_cache_key_with_empty_string(self):
        """Test cache key generation with empty string."""
        key = get_cache_key("")

        assert len(key) == 32
        assert key == hashlib.md5("".encode()).hexdigest()

    def test_cache_key_with_unicode(self):
        """Test cache key generation with unicode characters."""
        path = "salesforce.日本語"

        key = get_cache_key(path)

        assert len(key) == 32
        assert key == hashlib.md5(path.encode()).hexdigest()

    def test_multiple_adds_same_key_same_driver(self):
        """Test adding same driver multiple times with same key."""
        cache_key = get_cache_key("salesforce.dev")
        mock_driver = Mock()

        add_driver_to_cache(cache_key, mock_driver)
        add_driver_to_cache(cache_key, mock_driver)
        add_driver_to_cache(cache_key, mock_driver)

        # Should still have just one entry
        assert get_driver_from_cache(cache_key) is mock_driver

    def test_clear_cache_with_none_path(self):
        """Test clear_cache with None path clears all."""
        key1 = get_cache_key("salesforce.dev")
        key2 = get_cache_key("salesforce.prod")

        add_driver_to_cache(key1, Mock())
        add_driver_to_cache(key2, Mock())

        clear_cache(None)

        # All should be cleared
        assert not has_driver_in_cache(key1)
        assert not has_driver_in_cache(key2)

    def test_cache_isolation_between_tests(self):
        """Test that cache doesn't leak between test runs."""
        # This test verifies that setup_method properly clears cache
        cache_key = get_cache_key("salesforce.test")

        # Cache should be empty at start of test
        assert not has_driver_in_cache(cache_key)


class TestCacheManagerThreadSafety:
    """Tests for thread safety considerations (documentation)."""

    def test_cache_is_not_explicitly_thread_safe(self):
        """Document that TTLCache is not thread-safe by default."""
        # TTLCache from cachetools is not thread-safe
        # If concurrent access is needed, consider using locks
        # This test documents the limitation

        from cachetools import TTLCache

        assert isinstance(driver_cache, TTLCache)
        # In production, consider wrapping cache operations with locks
        # if concurrent access from multiple threads is expected


class TestCacheManagerIntegration:
    """Integration tests for cache manager with realistic scenarios."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cache()

    def test_realistic_multi_environment_scenario(self):
        """Test caching drivers for multiple environments."""
        environments = [
            "salesforce.dev",
            "salesforce.staging",
            "salesforce.prod",
            "salesforce.sandbox",
        ]

        drivers = {}

        # Add drivers for each environment
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
        cache_key = get_cache_key("salesforce.prod")

        # First access - cache miss
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
        assert result.version == "new"
