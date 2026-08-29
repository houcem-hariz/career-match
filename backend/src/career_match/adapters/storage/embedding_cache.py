"""Disk cache for embedding vectors.

Key = SHA-256 of the text + text version + model id. Changing any of the three must
bust the cache, otherwise a stale vector would silently hide a behaviour change.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


class EmbeddingCache:
    def __init__(self, directory: Path, enabled: bool = True) -> None:
        self.directory = directory
        self.enabled = enabled
        if enabled:
            self.directory.mkdir(parents=True, exist_ok=True)

    def key(self, text: str, text_version: str, model: str) -> str:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        material = f"{digest}:{text_version}:{model}"
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    def get(self, cache_key: str) -> list[float] | None:
        if not self.enabled:
            return None
        path = self.directory / f"{cache_key}.json"
        if not path.exists():
            return None
        loaded: object = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, list) or not loaded:
            return None
        return [float(item) for item in loaded]

    def put(self, cache_key: str, vector: list[float]) -> None:
        if not self.enabled:
            return
        path = self.directory / f"{cache_key}.json"
        path.write_text(json.dumps(vector), encoding="utf-8")
