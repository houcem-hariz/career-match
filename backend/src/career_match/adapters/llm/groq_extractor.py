"""Groq implementation of the profile and offer-skill extractors (GPT-OSS 20B)."""

from __future__ import annotations

from career_match.adapters.llm.chat import ChatOfferSkillExtractor, ChatProfileExtractor
from career_match.adapters.llm.prompts import parse_profile_payload
from career_match.settings import Settings

# Re-export: existing tests and callers import the parser from this module.
__all__ = [
    "GroqOfferSkillExtractor",
    "GroqProfileExtractor",
    "parse_profile_payload",
]


class GroqProfileExtractor(ChatProfileExtractor):
    def __init__(self, settings: Settings) -> None:
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is missing. Put it in the project .env file.")
        super().__init__(
            model_id=settings.llm_chat_model,
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
        )


class GroqOfferSkillExtractor(ChatOfferSkillExtractor):
    def __init__(self, settings: Settings) -> None:
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is missing. Put it in the project .env file.")
        super().__init__(
            model_id=settings.llm_chat_model,
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
        )
