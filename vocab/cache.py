"""JSON disk cache with 30-day TTL."""

import hashlib
import json
import time
from pathlib import Path

DEFAULT_CACHE_DIR = Path.home() / ".cache" / "vocab"
TTL_SECONDS = 30 * 24 * 3600  # 30 days


class DiskCache:
    def __init__(self, cache_dir: Path = DEFAULT_CACHE_DIR):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key_path(self, word: str) -> Path:
        h = hashlib.sha256(word.lower().encode()).hexdigest()[:16]
        return self.cache_dir / f"{h}.json"

    def get(self, word: str) -> dict | None:
        path = self._key_path(word)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            if time.time() - data.get("_ts", 0) > TTL_SECONDS:
                path.unlink(missing_ok=True)
                return None
            return data.get("payload")
        except (json.JSONDecodeError, OSError):
            return None

    def clear(self) -> int:
        """Remove all cached entries. Returns number of files removed."""
        count = 0
        for f in self.cache_dir.glob("*.json"):
            f.unlink(missing_ok=True)
            count += 1
        return count

    def set(self, word: str, payload: dict) -> None:
        path = self._key_path(word)
        try:
            path.write_text(json.dumps({"_ts": time.time(), "payload": payload}))
        except OSError:
            pass
