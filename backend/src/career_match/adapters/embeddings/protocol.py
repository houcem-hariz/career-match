"""Provider-agnostic embedding contract.

The rest of the pipeline depends on this interface, never on OpenAI or Ollama directly.
Changing the model id or the text version busts the disk cache and requires a re-index.
"""

from typing import Protocol

EMBEDDING_TEXT_VERSION = "offer-title-desc-v1"
DEFAULT_EMBEDDING_DIMENSIONS = 1536


class Embedder(Protocol):
    model_id: str
    dimensions: int

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order."""
        ...
