"""Disk cache for LLM extractions.

Key = SHA-256 of the source bytes + prompt version + model id. Changing the prompt or
the model must bust the cache, otherwise a stale JSON would silently hide a behaviour
change. The demo can run from cache without a network call.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class ExtractionCache:
    def __init__(self, directory: Path, enabled: bool = True) -> None:
        self.directory = directory
        self.enabled = enabled
        if enabled:
            self.directory.mkdir(parents=True, exist_ok=True)

    def key(self, source_bytes: bytes, prompt_version: str, model: str) -> str:
        digest = hashlib.sha256(source_bytes).hexdigest()
        material = f"{digest}:{prompt_version}:{model}"
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    def get(self, cache_key: str) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        path = self.directory / f"{cache_key}.json"
        if not path.exists():
            return None
        loaded: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return loaded

    def put(self, cache_key: str, payload: dict[str, Any]) -> None:
        if not self.enabled:
            return
        path = self.directory / f"{cache_key}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
