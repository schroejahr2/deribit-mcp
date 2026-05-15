"""In-memory price cache with per-key freshness tracking."""

from __future__ import annotations

import time
from typing import Dict, Iterator, MutableMapping, Optional


class PriceCache(MutableMapping[str, float]):
    """Instrument price store that records the last-update timestamp per key.

    Behaves like ``Dict[str, float]`` for existing readers (``in``, ``[]``,
    ``items()``, ``len()``) so legacy callers keep working unchanged. Adds
    ``age_seconds()`` so callers can decide whether the cached value is fresh
    enough to use before time-sensitive decisions (e.g. trigger-price checks).
    """

    def __init__(self, initial: Optional[Dict[str, float]] = None) -> None:
        self._prices: Dict[str, float] = {}
        self._ts: Dict[str, float] = {}
        if initial:
            for key, value in initial.items():
                self[key] = value

    def __getitem__(self, key: str) -> float:
        return self._prices[key]

    def __setitem__(self, key: str, value: float) -> None:
        self._prices[key] = float(value)
        self._ts[key] = time.time()

    def __delitem__(self, key: str) -> None:
        self._prices.pop(key, None)
        self._ts.pop(key, None)

    def __iter__(self) -> Iterator[str]:
        return iter(self._prices)

    def __len__(self) -> int:
        return len(self._prices)

    def __contains__(self, key: object) -> bool:
        return key in self._prices

    def age_seconds(self, key: str) -> Optional[float]:
        """Seconds since the value for ``key`` was written. ``None`` if absent."""
        ts = self._ts.get(key)
        if ts is None:
            return None
        return max(0.0, time.time() - ts)

    def updated_at(self, key: str) -> Optional[float]:
        """Epoch seconds when the value for ``key`` was last written."""
        return self._ts.get(key)
