"""Very small in-memory TTL cache for discovery-heavy calls."""
from __future__ import annotations

import time
from typing import Any, Dict, Hashable, Tuple

from aws_helper.constants import DISCOVERY_CACHE_TTL_SECONDS

_CACHE: Dict[Tuple[Hashable, ...], Tuple[float, Any]] = {}


def get_or_set(key: Tuple[Hashable, ...], factory, ttl_seconds: int = DISCOVERY_CACHE_TTL_SECONDS):
    now = time.time()
    if key in _CACHE:
        expires_at, value = _CACHE[key]
        if now < expires_at:
            return value
    value = factory()
    _CACHE[key] = (now + ttl_seconds, value)
    return value


def clear_cache() -> None:
    _CACHE.clear()
