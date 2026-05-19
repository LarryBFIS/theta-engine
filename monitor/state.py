"""State persistence — tracks last-fired times for each alert to enforce cooldowns."""
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


class State:
    """Simple JSON-backed state. Tracks last fire time per alert key."""

    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                with open(self.path) as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                log.warning("Could not read state file %s: %s — starting fresh", self.path, e)
                self._data = {}
        else:
            self._data = {}

    def _save(self) -> None:
        try:
            tmp = self.path.with_suffix(".tmp")
            with open(tmp, "w") as f:
                json.dump(self._data, f, indent=2, default=str)
            os.replace(tmp, self.path)
        except OSError as e:
            log.error("Could not save state to %s: %s", self.path, e)

    def last_fired(self, key: str) -> Optional[datetime]:
        ts = self._data.get(key)
        if not ts:
            return None
        try:
            return datetime.fromisoformat(ts)
        except (ValueError, TypeError):
            return None

    def mark_fired(self, key: str) -> None:
        self._data[key] = datetime.now(timezone.utc).isoformat()
        self._save()

    def cooldown_ok(self, key: str, minutes: int) -> bool:
        """Return True if it's been longer than `minutes` since this key last fired."""
        last = self.last_fired(key)
        if not last:
            return True
        elapsed = (datetime.now(timezone.utc) - last).total_seconds() / 60
        return elapsed >= minutes

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        self._data[key] = value
        self._save()
