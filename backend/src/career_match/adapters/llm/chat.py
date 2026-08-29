"""OpenAI-compatible chat client used by Groq and OpenAI extractors."""

from __future__ import annotations

import json

from langchain_openai import ChatOpenAI

from career_match.adapters.llm.prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    OFFER_SKILLS_PROMPT,
    parse_profile_payload,
    parse_skill_list_payload,
)
from career_match.domain.models.profile import RawProfile


class ChatProfileExtractor:
    """One ChatOpenAI client. Groq and OpenAI only differ by key, URL, and model id."""

    def __init__(self, *, model_id: str, api_key: str, base_url: str) -> None:
        self.model_id = model_id
        self._llm = ChatOpenAI(
            model=model_id,
            api_key=api_key,
            base_url=base_url,
            temperature=0,
        ).bind(response_format={"type": "json_object"})

    def extract_profile(self, cv_text: str) -> RawProfile:
        schema = json.dumps(RawProfile.model_json_schema(), ensure_ascii=False)
        message = self._llm.invoke(
            [
                {
                    "role": "system",
                    "content": EXTRACTION_SYSTEM_PROMPT + "\n\nJSON schema:\n" + schema,
                },
                {"role": "user", "content": cv_text},
            ]
        )
        return parse_profile_payload(_message_text(message.content))


class ChatOfferSkillExtractor:
    def __init__(self, *, model_id: str, api_key: str, base_url: str) -> None:
        self.model_id = model_id
        self._llm = ChatOpenAI(
            model=model_id,
            api_key=api_key,
            base_url=base_url,
            temperature=0,
        )

    def extract_skills(self, offer_text: str) -> list[str]:
        message = self._llm.invoke(
            [
                {"role": "system", "content": OFFER_SKILLS_PROMPT},
                {"role": "user", "content": offer_text[:4000]},
            ]
        )
        return parse_skill_list_payload(_message_text(message.content))


def _message_text(content: object) -> str:
    if isinstance(content, str):
        return content
    return str(content)
