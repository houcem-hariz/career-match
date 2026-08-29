"""Unit tests for eliminating retrieval filters and the profile search text."""

from career_match.domain.models.enums import JobFamily, SkillLevel, WorkModel
from career_match.domain.models.profile import Profile, WorkPreferences
from career_match.domain.models.skill import NormalizedSkill
from career_match.domain.retrieval.filters import RetrievalFilters, passes_filters
from career_match.domain.retrieval.query import profile_search_text


def _profile(**kwargs: object) -> Profile:
    defaults: dict[str, object] = {"profile_id": "p1"}
    defaults.update(kwargs)
    return Profile.model_validate(defaults)


def test_empty_filters_pass_everything() -> None:
    filters = RetrievalFilters.from_profile(_profile())
    assert passes_filters(
        family=JobFamily.DATA,
        location_text="Paris",
        work_model="onsite",
        filters=filters,
    )


def test_family_filter_is_eliminating() -> None:
    filters = RetrievalFilters.from_profile(_profile(target_families=[JobFamily.BACKEND]))
    assert passes_filters(
        family=JobFamily.BACKEND,
        location_text=None,
        work_model=None,
        filters=filters,
    )
    assert not passes_filters(
        family=JobFamily.FRONTEND,
        location_text=None,
        work_model=None,
        filters=filters,
    )


def test_unknown_work_model_is_not_eliminated() -> None:
    filters = RetrievalFilters.from_profile(
        _profile(preferences=WorkPreferences(work_models=(WorkModel.REMOTE,)))
    )
    assert passes_filters(
        family=JobFamily.BACKEND,
        location_text=None,
        work_model=None,
        filters=filters,
    )
    assert not passes_filters(
        family=JobFamily.BACKEND,
        location_text=None,
        work_model="onsite",
        filters=filters,
    )


def test_location_substring_and_relocate_bypass() -> None:
    anchored = RetrievalFilters.from_profile(
        _profile(preferences=WorkPreferences(locations=("Toronto",)))
    )
    assert passes_filters(
        family=JobFamily.BACKEND,
        location_text="Toronto, Canada",
        work_model=None,
        filters=anchored,
    )
    assert not passes_filters(
        family=JobFamily.BACKEND,
        location_text="London, UK",
        work_model=None,
        filters=anchored,
    )
    relocating = RetrievalFilters.from_profile(
        _profile(preferences=WorkPreferences(locations=("Toronto",), willing_to_relocate=True))
    )
    assert passes_filters(
        family=JobFamily.BACKEND,
        location_text="London, UK",
        work_model=None,
        filters=relocating,
    )


def test_profile_search_text_uses_title_and_skill_ids() -> None:
    profile = _profile(
        target_title="Backend Engineer",
        target_families=[JobFamily.BACKEND],
        skills=[NormalizedSkill(skill_id="python", level=SkillLevel.WORKING)],
    )
    text = profile_search_text(profile)
    assert "Backend Engineer" in text
    assert "python" in text
    assert "backend" in text
