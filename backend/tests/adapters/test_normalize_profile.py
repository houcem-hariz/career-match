"""Load the committed referential and resolve real surface forms against it."""

from career_match.adapters.storage.referential_io import load_referential_index
from career_match.domain.models.enums import SkillLevel
from career_match.domain.models.profile import RawProfile
from career_match.domain.models.skill import RawSkill
from career_match.domain.normalization.cascade import normalize_profile
from career_match.settings import project_root

REFERENTIAL = project_root() / "data" / "processed" / "referentiel.json"


def test_committed_referential_resolves_common_aliases() -> None:
    index = load_referential_index(REFERENTIAL)
    raw = RawProfile(
        total_years_experience=7,
        skills=[
            RawSkill(label="React.js", level=SkillLevel.PROFICIENT),
            RawSkill(label="K8s"),
            RawSkill(label="Postgres"),
            RawSkill(label="Node.js"),
            RawSkill(label="teamwork"),
        ],
    )
    result = normalize_profile(raw, index, profile_id="p1")
    ids = {skill.skill_id for skill in result.profile.skills}
    assert {"react", "kubernetes", "postgresql", "nodejs"} <= ids
    reasons = {item.label: item.reason for item in result.unmatched}
    assert reasons["teamwork"] == "noise"
