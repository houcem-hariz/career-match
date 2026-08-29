"""Build LLM and embedding adapters from settings. Callers never import Groq or OpenAI."""

from __future__ import annotations

from career_match.adapters.embeddings.openai_embedder import OpenAIEmbedder
from career_match.adapters.embeddings.protocol import Embedder
from career_match.adapters.llm.chat import ChatOfferSkillExtractor, ChatProfileExtractor
from career_match.adapters.llm.groq_extractor import GroqOfferSkillExtractor, GroqProfileExtractor
from career_match.adapters.llm.openai_extractor import (
    OpenAIOfferSkillExtractor,
    OpenAIProfileExtractor,
)
from career_match.settings import Settings


class UnknownLlmProviderError(ValueError):
    """Raised when LLM_PROVIDER is not groq or openai."""


def build_profile_extractor(settings: Settings) -> ChatProfileExtractor:
    provider = settings.llm_provider.strip().lower()
    if provider == "groq":
        return GroqProfileExtractor(settings)
    if provider == "openai":
        return OpenAIProfileExtractor(settings)
    raise UnknownLlmProviderError(
        f"Unsupported LLM_PROVIDER={settings.llm_provider!r}. Use groq or openai."
    )


def build_offer_skill_extractor(settings: Settings) -> ChatOfferSkillExtractor:
    provider = settings.llm_provider.strip().lower()
    if provider == "groq":
        return GroqOfferSkillExtractor(settings)
    if provider == "openai":
        return OpenAIOfferSkillExtractor(settings)
    raise UnknownLlmProviderError(
        f"Unsupported LLM_PROVIDER={settings.llm_provider!r}. Use groq or openai."
    )


def build_embedder(settings: Settings) -> Embedder:
    return OpenAIEmbedder(settings)
