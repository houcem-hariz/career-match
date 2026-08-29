"""OpenAI implementation of the profile and offer-skill extractors."""

from __future__ import annotations

from career_match.adapters.llm.chat import ChatOfferSkillExtractor, ChatProfileExtractor
from career_match.settings import Settings


class OpenAIProfileExtractor(ChatProfileExtractor):
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is missing. Put it in the project .env file.")
        super().__init__(
            model_id=settings.openai_chat_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )


class OpenAIOfferSkillExtractor(ChatOfferSkillExtractor):
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is missing. Put it in the project .env file.")
        super().__init__(
            model_id=settings.openai_chat_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
