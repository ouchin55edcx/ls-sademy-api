"""
Utility helpers for working with cache entries.
"""
from __future__ import annotations

from django.core.cache import caches


def invalidate_cache_prefix(prefix: str) -> None:
    """
    Remove all cache entries that start with the provided prefix.

    This relies on django-redis' ``delete_pattern`` implementation.
    """
    cache = caches["default"]
    pattern = f"{prefix}*"
    try:
        cache.delete_pattern(pattern)
    except NotImplementedError:
        # Fallback for cache backends without delete_pattern support.
        pass

