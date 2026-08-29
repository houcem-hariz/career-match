"""OpenAI implementation of the embedder (text-embedding-3-small)."""

from __future__ import annotations

import time

from openai import APIConnectionError, OpenAI, RateLimitError

from career_match.settings import Settings

_BATCH_SIZE = 32
_MAX_ATTEMPTS = 4


class OpenAIEmbedder:
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is missing. Put it in the project .env file.")
        self.model_id = settings.llm_embedding_model
        self.dimensions = settings.embedding_dimensions
        self._client = OpenAI(api_key=settings.openai_api_key)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors: list[list[float]] = []
        for start in range(0, len(texts), _BATCH_SIZE):
            chunk = texts[start : start + _BATCH_SIZE]
            vectors.extend(self._embed_chunk(chunk))
        return vectors

    def _embed_chunk(self, texts: list[str]) -> list[list[float]]:
        last_error: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            try:
                response = self._client.embeddings.create(
                    model=self.model_id,
                    input=texts,
                    dimensions=self.dimensions,
                )
                ordered = sorted(response.data, key=lambda item: item.index)
                return [list(item.embedding) for item in ordered]
            except (RateLimitError, APIConnectionError) as exc:
                last_error = exc
                if attempt == _MAX_ATTEMPTS - 1:
                    break
                time.sleep(2**attempt)
        assert last_error is not None
        raise last_error
