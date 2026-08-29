"""Build the text that is embedded for semantic retrieval.

The offer side embeds title + description. The profile side must stay in the same
semantic space without inventing prose: title, families, normalised skill ids, experience
titles. Scoring (week 3) is a separate step and does not belong here.
"""

from career_match.domain.models.profile import Profile

PROFILE_SEARCH_TEXT_VERSION = "profile-search-v1"


def profile_search_text(profile: Profile) -> str:
    parts: list[str] = []
    if profile.target_title:
        parts.append(profile.target_title)
    if profile.target_families:
        parts.append(" ".join(family.value.replace("_", " ") for family in profile.target_families))
    if profile.skills:
        parts.append(" ".join(skill.skill_id.replace("_", " ") for skill in profile.skills))
    for experience in profile.experiences:
        if experience.title:
            parts.append(experience.title)
    return "\n".join(parts) if parts else "software engineer"
