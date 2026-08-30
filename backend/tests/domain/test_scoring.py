"""Six-dimension scoring, buckets, gaps and impact simulation."""

import pytest
from pydantic import ValidationError

from career_match.domain.models.enums import (
    EducationLevel,
    JobFamily,
    LanguageProficiency,
    MatchBucket,
    SeniorityLevel,
    SkillLevel,
    SkillRequirement,
)
from career_match.domain.models.offer import Offer, RequiredLanguage
from career_match.domain.models.profile import EducationRecord, LanguageSkill, Profile
from career_match.domain.models.skill import NormalizedSkill, RequiredSkill
from career_match.domain.scoring.catalog import TrainingCourse, apply_course
from career_match.domain.scoring.config import ScoringConfig, ScoringWeights
from career_match.domain.scoring.score import score_offer
from career_match.domain.scoring.simulate import simulate_course, simulate_mandatory_gaps


def _profile(**kwargs: object) -> Profile:
    defaults: dict[str, object] = {
        "profile_id": "p1",
        "seniority": SeniorityLevel.SENIOR,
        "skills": [
            NormalizedSkill(skill_id="python", level=SkillLevel.PROFICIENT),
            NormalizedSkill(skill_id="kubernetes", level=SkillLevel.AWARENESS),
        ],
        "education": [EducationRecord(level=EducationLevel.BACHELOR)],
        "languages": [LanguageSkill(language_code="en", proficiency=LanguageProficiency.C1)],
    }
    defaults.update(kwargs)
    return Profile.model_validate(defaults)


def _offer(**kwargs: object) -> Offer:
    defaults: dict[str, object] = {
        "offer_id": "o1",
        "source_id": "o1",
        "title": "Backend Engineer",
        "family": JobFamily.BACKEND,
        "seniority": SeniorityLevel.SENIOR,
        "required_skills": [
            RequiredSkill(
                skill_id="python",
                requirement=SkillRequirement.MANDATORY,
                minimum_level=SkillLevel.WORKING,
            ),
            RequiredSkill(
                skill_id="kubernetes",
                requirement=SkillRequirement.MANDATORY,
                minimum_level=SkillLevel.WORKING,
            ),
            RequiredSkill(
                skill_id="kafka",
                requirement=SkillRequirement.PREFERRED,
                minimum_level=SkillLevel.WORKING,
            ),
        ],
        "minimum_education": EducationLevel.BACHELOR,
        "required_languages": [
            RequiredLanguage(language_code="en", minimum_proficiency=LanguageProficiency.B2)
        ],
    }
    defaults.update(kwargs)
    return Offer.model_validate(defaults)


def test_weights_must_sum_to_one() -> None:
    with pytest.raises(ValidationError):
        ScoringWeights(mandatory_skills=0.5, preferred_skills=0.5, seniority=0.5)


def test_perfect_enough_match_is_reachable_because_of_k8s_level() -> None:
    breakdown = score_offer(_profile(), _offer(), semantic_similarity=0.8)
    assert breakdown.bucket is MatchBucket.REACHABLE
    assert breakdown.mandatory_gap_count == 1
    assert any(gap.skill_id == "kubernetes" for gap in breakdown.gaps)
    assert 50 < breakdown.total < 90


def test_closing_the_k8s_gap_makes_the_offer_eligible() -> None:
    profile = _profile(
        skills=[
            NormalizedSkill(skill_id="python", level=SkillLevel.PROFICIENT),
            NormalizedSkill(skill_id="kubernetes", level=SkillLevel.WORKING),
        ]
    )
    breakdown = score_offer(profile, _offer(), semantic_similarity=0.8)
    assert breakdown.bucket is MatchBucket.ELIGIBLE
    assert breakdown.mandatory_gap_count == 0
    assert breakdown.dimensions["mandatory_skills"] == 1.0


def test_three_missing_mandatories_are_out_of_reach() -> None:
    offer = _offer(
        required_skills=[
            RequiredSkill(skill_id="python", requirement=SkillRequirement.MANDATORY),
            RequiredSkill(skill_id="java", requirement=SkillRequirement.MANDATORY),
            RequiredSkill(skill_id="go", requirement=SkillRequirement.MANDATORY),
            RequiredSkill(skill_id="scala", requirement=SkillRequirement.MANDATORY),
        ]
    )
    profile = _profile(skills=[NormalizedSkill(skill_id="python", level=SkillLevel.WORKING)])
    breakdown = score_offer(profile, offer, semantic_similarity=0.2)
    assert breakdown.mandatory_gap_count == 3
    assert breakdown.bucket is MatchBucket.OUT_OF_REACH


def test_junior_versus_lead_is_out_of_reach_even_with_skills() -> None:
    profile = _profile(
        seniority=SeniorityLevel.JUNIOR,
        skills=[
            NormalizedSkill(skill_id="python", level=SkillLevel.WORKING),
            NormalizedSkill(skill_id="kubernetes", level=SkillLevel.WORKING),
        ],
    )
    offer = _offer(seniority=SeniorityLevel.LEAD)
    breakdown = score_offer(profile, offer, semantic_similarity=0.9)
    assert breakdown.seniority_gap == -3
    assert breakdown.bucket is MatchBucket.OUT_OF_REACH


def test_preferred_gap_does_not_change_the_bucket() -> None:
    profile = _profile(
        skills=[
            NormalizedSkill(skill_id="python", level=SkillLevel.WORKING),
            NormalizedSkill(skill_id="kubernetes", level=SkillLevel.WORKING),
        ]
    )
    with_pref = score_offer(profile, _offer(), semantic_similarity=0.7)
    offer = _offer(
        required_skills=[
            RequiredSkill(skill_id="python", requirement=SkillRequirement.MANDATORY),
            RequiredSkill(skill_id="kubernetes", requirement=SkillRequirement.MANDATORY),
        ]
    )
    without_pref = score_offer(profile, offer, semantic_similarity=0.7)
    assert with_pref.bucket is without_pref.bucket is MatchBucket.ELIGIBLE
    assert with_pref.total < without_pref.total


def test_no_requirements_score_full_on_structured_axes() -> None:
    offer = _offer(required_skills=[], required_languages=[], minimum_education=EducationLevel.NONE)
    breakdown = score_offer(_profile(), offer, semantic_similarity=0.0)
    assert breakdown.dimensions["mandatory_skills"] == 1.0
    assert breakdown.dimensions["preferred_skills"] == 1.0
    assert breakdown.dimensions["education"] == 1.0
    assert breakdown.dimensions["languages"] == 1.0
    assert breakdown.dimensions["semantic"] == 0.0


def test_simulation_raises_score_and_can_move_bucket() -> None:
    course = TrainingCourse(
        course_id="k8s-fundamentals",
        title="Kubernetes fundamentals",
        skill_id="kubernetes",
        target_level=SkillLevel.WORKING,
    )
    impact = simulate_course(_profile(), _offer(), course, semantic_similarity=0.8)
    assert impact.delta > 0
    assert impact.before.bucket is MatchBucket.REACHABLE
    assert impact.after.bucket is MatchBucket.ELIGIBLE


def test_simulate_mandatory_gaps_picks_catalog_courses() -> None:
    catalogue = [
        TrainingCourse(
            course_id="k8s-fundamentals",
            title="Kubernetes fundamentals",
            skill_id="kubernetes",
            target_level=SkillLevel.WORKING,
        )
    ]
    results = simulate_mandatory_gaps(_profile(), _offer(), 0.8, catalogue)
    assert len(results) == 1
    assert results[0].course.course_id == "k8s-fundamentals"


def test_apply_course_inserts_a_missing_skill() -> None:
    course = TrainingCourse(course_id="aws", title="AWS", skill_id="aws")
    updated = apply_course(_profile(), course)
    assert updated.skill_by_id("aws") is not None
    assert updated.skill_by_id("aws").level is SkillLevel.WORKING


def test_scoring_config_is_frozen_data() -> None:
    config = ScoringConfig()
    assert abs(config.weights.mandatory_skills + config.weights.semantic - 0.55) < 1e-9
