import threading
import time

from app import config


class TTLDeduplicator:
    def __init__(self, ttl_seconds: float) -> None:
        self._ttl = ttl_seconds
        self._seen: dict[str, float] = {}
        self._lock = threading.Lock()

    def claim(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            for stale in [item for item, expiry in self._seen.items() if expiry <= now]:
                del self._seen[stale]
            if key in self._seen:
                return False
            self._seen[key] = now + self._ttl
            return True


deduplicator = TTLDeduplicator(config.DEDUPE_TTL_SECONDS)
