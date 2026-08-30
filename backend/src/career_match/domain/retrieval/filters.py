"""Deterministic retrieval filters applied before semantic similarity."""

from __future__ import annotations

from dataclasses import dataclass

from career_match.domain.models.enums import JobFamily
from career_match.domain.models.profile import Profile


@dataclass(frozen=True)
class RetrievalFilters:
    """Eliminating constraints. Empty collections mean 'no constraint on this axis'."""

    families: tuple[JobFamily, ...] = ()
    locations: tuple[str, ...] = ()
    work_models: tuple[str, ...] = ()
    apply_location: bool = False

    @classmethod
    def from_profile(cls, profile: Profile) -> RetrievalFilters:
        locations = tuple(loc.strip() for loc in profile.preferences.locations if loc.strip())
        return cls(
            families=tuple(profile.target_families),
            locations=locations,
            work_models=tuple(model.value for model in profile.preferences.work_models),
            apply_location=bool(locations) and not profile.preferences.willing_to_relocate,
        )


def passes_filters(
    *,
    family: JobFamily,
    location_text: str | None,
    work_model: str | None,
    filters: RetrievalFilters,
) -> bool:
    if filters.families and family not in filters.families:
        return False
    if filters.work_models and work_model is not None and work_model not in filters.work_models:
        return False
    if filters.apply_location and location_text is not None:
        if not location_matches(location_text, filters.locations):
            return False
    return True


def location_matches(location_text: str, needles: tuple[str, ...]) -> bool:
    haystack = location_text.casefold()
    return any(needle.casefold() in haystack for needle in needles)
