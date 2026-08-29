"""Provider factory: CLI depends on the interface, not on Groq or OpenAI."""

from pathlib import Path

import pytest

from career_match.adapters.embeddings.openai_embedder import OpenAIEmbedder
from career_match.adapters.llm.factory import (
    UnknownLlmProviderError,
    build_embedder,
    build_offer_skill_extractor,
    build_profile_extractor,
)
from career_match.adapters.llm.groq_extractor import GroqOfferSkillExtractor, GroqProfileExtractor
from career_match.adapters.llm.openai_extractor import (
    OpenAIOfferSkillExtractor,
    OpenAIProfileExtractor,
)
from career_match.settings import Settings


def _settings(**overrides: object) -> Settings:
    payload: dict[str, object] = {
        "llm_provider": "groq",
        "llm_chat_model": "openai/gpt-oss-20b",
        "groq_api_key": "gsk_test",
        "groq_base_url": "https://api.groq.com/openai/v1",
        "openai_api_key": "sk-test",
        "openai_chat_model": "gpt-4o-mini",
        "openai_base_url": "https://api.openai.com/v1",
        "llm_embedding_model": "text-embedding-3-small",
        "embedding_dimensions": 1536,
        "database_url": "postgresql://career_match:career_match@127.0.0.1:5433/career_match",
        "extraction_cache_enabled": True,
        "extraction_cache_dir": Path("."),
        "embedding_cache_dir": Path("."),
    }
    payload.update(overrides)
    return Settings.model_construct(**payload)


def test_factory_selects_groq_extractor() -> None:
    extractor = build_profile_extractor(_settings(llm_provider="groq"))
    assert isinstance(extractor, GroqProfileExtractor)
    assert extractor.model_id == "openai/gpt-oss-20b"


def test_factory_selects_openai_extractor() -> None:
    extractor = build_profile_extractor(_settings(llm_provider="openai"))
    assert isinstance(extractor, OpenAIProfileExtractor)
    assert extractor.model_id == "gpt-4o-mini"


def test_factory_selects_matching_offer_skill_extractor() -> None:
    groq = build_offer_skill_extractor(_settings(llm_provider="GROQ"))
    openai = build_offer_skill_extractor(_settings(llm_provider="openai"))
    assert isinstance(groq, GroqOfferSkillExtractor)
    assert isinstance(openai, OpenAIOfferSkillExtractor)


def test_factory_rejects_unknown_provider() -> None:
    with pytest.raises(UnknownLlmProviderError, match="anthropic"):
        build_profile_extractor(_settings(llm_provider="anthropic"))


def test_factory_requires_provider_key() -> None:
    with pytest.raises(ValueError, match="GROQ_API_KEY"):
        build_profile_extractor(_settings(llm_provider="groq", groq_api_key=""))
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        build_profile_extractor(_settings(llm_provider="openai", openai_api_key=""))


def test_build_embedder_returns_openai() -> None:
    embedder = build_embedder(_settings())
    assert isinstance(embedder, OpenAIEmbedder)
    assert embedder.model_id == "text-embedding-3-small"
