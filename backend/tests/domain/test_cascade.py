"""Deterministic normalisation cascade (exact, alias, fuzzy) and seniority."""

from career_match.domain.models.enums import JobFamily, SeniorityLevel, SkillLevel
from career_match.domain.models.profile import RawProfile
from career_match.domain.models.skill import RawSkill, ReferenceSkill
from career_match.domain.normalization.cascade import (
    ReferentialIndex,
    normalize_profile,
    seniority_from_years,
)


def _index() -> ReferentialIndex:
    return ReferentialIndex(
        [
            ReferenceSkill(
                skill_id="react",
                canonical_label="React",
                aliases=("React", "React.js", "ReactJS"),
                families=(JobFamily.FRONTEND,),
                occurrences=10,
            ),
            ReferenceSkill(
                skill_id="kubernetes",
                canonical_label="Kubernetes",
                aliases=("Kubernetes", "K8s"),
                families=(JobFamily.DEVOPS,),
                occurrences=8,
            ),
            ReferenceSkill(
                skill_id="postgresql",
                canonical_label="PostgreSQL",
                aliases=("PostgreSQL", "Postgres"),
                families=(JobFamily.BACKEND,),
                occurrences=6,
            ),
            ReferenceSkill(
                skill_id="javascript",
                canonical_label="JavaScript",
                aliases=("JavaScript", "JS"),
                families=(JobFamily.FRONTEND,),
                occurrences=5,
            ),
            ReferenceSkill(
                skill_id="java",
                canonical_label="Java",
                aliases=("Java",),
                families=(JobFamily.BACKEND,),
                occurrences=5,
            ),
            ReferenceSkill(
                skill_id="abcdefghij",
                canonical_label="abcdefghij",
                aliases=("abcdefghij",),
                families=(JobFamily.BACKEND,),
                occurrences=1,
            ),
            ReferenceSkill(
                skill_id="abcdefghik",
                canonical_label="abcdefghik",
                aliases=("abcdefghik",),
                families=(JobFamily.BACKEND,),
                occurrences=1,
            ),
        ]
    )


def test_seniority_thresholds() -> None:
    assert seniority_from_years(0) is SeniorityLevel.JUNIOR
    assert seniority_from_years(1.5) is SeniorityLevel.JUNIOR
    assert seniority_from_years(2) is SeniorityLevel.MID
    assert seniority_from_years(4.9) is SeniorityLevel.MID
    assert seniority_from_years(5) is SeniorityLevel.SENIOR
    assert seniority_from_years(10) is SeniorityLevel.LEAD


def test_exact_and_alias_and_canonical_map() -> None:
    index = _index()
    raw = RawProfile(
        total_years_experience=6,
        skills=[
            RawSkill(label="React.js", level=SkillLevel.PROFICIENT),
            RawSkill(label="K8s", level=SkillLevel.AWARENESS),
            RawSkill(label="Postgres", level=SkillLevel.WORKING),
        ],
    )
    result = normalize_profile(raw, index, profile_id="p1")
    ids = {skill.skill_id: skill for skill in result.profile.skills}
    assert set(ids) == {"react", "kubernetes", "postgresql"}
    assert ids["react"].level is SkillLevel.PROFICIENT
    assert result.profile.seniority is SeniorityLevel.SENIOR
    assert result.unmatched == ()


def test_java_does_not_match_javascript() -> None:
    index = _index()
    raw = RawProfile(skills=[RawSkill(label="Java", level=SkillLevel.WORKING)])
    result = normalize_profile(raw, index, profile_id="p1")
    assert [skill.skill_id for skill in result.profile.skills] == ["java"]


def test_unknown_and_noise_are_logged() -> None:
    index = _index()
    raw = RawProfile(
        skills=[
            RawSkill(label="GraphQL"),
            RawSkill(label="teamwork"),
        ]
    )
    result = normalize_profile(raw, index, profile_id="p1")
    assert result.profile.skills == []
    reasons = {item.label: item.reason for item in result.unmatched}
    assert reasons["GraphQL"] == "unknown"
    assert reasons["teamwork"] == "noise"


def test_missing_level_defaults_to_working() -> None:
    index = _index()
    raw = RawProfile(skills=[RawSkill(label="React")])
    result = normalize_profile(raw, index, profile_id="p1")
    assert result.profile.skills[0].level is SkillLevel.WORKING


def test_duplicate_labels_keep_the_higher_level_and_years() -> None:
    index = _index()
    raw = RawProfile(
        skills=[
            RawSkill(label="React.js", level=SkillLevel.WORKING, years_experience=4),
            RawSkill(label="React", level=SkillLevel.EXPERT, years_experience=2),
        ]
    )
    result = normalize_profile(raw, index, profile_id="p1")
    assert len(result.profile.skills) == 1
    assert result.profile.skills[0].level is SkillLevel.EXPERT
    assert result.profile.skills[0].years_experience == 4


def test_fuzzy_recovers_a_close_typo() -> None:
    index = _index()
    raw = RawProfile(skills=[RawSkill(label="postgressql")])
    result = normalize_profile(raw, index, profile_id="p1")
    assert [skill.skill_id for skill in result.profile.skills] == ["postgresql"]
    assert result.unmatched == ()


def test_equally_close_fuzzy_matches_are_ambiguous() -> None:
    index = _index()
    raw = RawProfile(skills=[RawSkill(label="abcdefghix")])
    result = normalize_profile(raw, index, profile_id="p1")
    assert result.profile.skills == []
    assert result.unmatched[0].reason == "ambiguous"
