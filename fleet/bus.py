"""Message bus — durable queue for fleet coordination.

A simple file-backed queue (JSONL persistence) instead of SQLite for
simplicity. Each message is witnessed via FNV-1a hash.
"""
import datetime
import json
import os
import time
from collections import deque
from pathlib import Path
from typing import Dict, List, Optional


from .core import fnv1a_64


BUS_PATH = Path("/workspace/research/mavis-fleet/bus.jsonl")
BUS_PATH.parent.mkdir(parents=True, exist_ok=True)


class MessageBus:
    """A persistent message queue for fleet coordination."""

    def __init__(self, path: Path = BUS_PATH):
        self.path = path
        self._cache: deque = deque()
        self._load_cache()

    def _load_cache(self):
        if self.path.exists():
            for line in self.path.read_text().strip().splitlines():
                try:
                    self._cache.append(json.loads(line))
                except Exception:
                    pass

    def publish(self, topic: str, payload: Dict, publisher: str = "fleet") -> str:
        """Publish a message to a topic."""
        msg = {
            "id": f"msg-{int(time.time() * 1000)}",
            "topic": topic,
            "payload": payload,
            "publisher": publisher,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        }
        # Compute hash for witness
        canonical = json.dumps(msg, sort_keys=True)
        msg["hash"] = f"0x{fnv1a_64(canonical):016x}"

        self._cache.append(msg)
        with self.path.open("a") as f:
            f.write(json.dumps(msg) + "\n")

        return msg["id"]

    def subscribe(self, topic: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get recent messages, optionally filtered by topic."""
        matches = []
        for msg in reversed(self._cache):
            if topic is None or msg.get("topic") == topic:
                matches.append(msg)
            if len(matches) >= limit:
                break
        return list(reversed(matches))

    def topics(self) -> List[str]:
        """List all known topics."""
        return sorted(set(msg.get("topic", "unknown") for msg in self._cache))

    def count(self, topic: Optional[str] = None) -> int:
        """Count messages, optionally per topic."""
        if topic is None:
            return len(self._cache)
        return sum(1 for m in self._cache if m.get("topic") == topic)
