"""Build a structured Offer from corpus annotations and the skill referential."""

from career_match.adapters.ingestion.structure_offer import MANDATORY_SKILL_CAP, structure_offer
from career_match.domain.models.enums import JobFamily, SeniorityLevel, SkillRequirement
from career_match.domain.models.offer import RawOffer
from career_match.domain.models.skill import ReferenceSkill
from career_match.domain.normalization.cascade import ReferentialIndex


def _index() -> ReferentialIndex:
    return ReferentialIndex(
        [
            ReferenceSkill(
                skill_id="python",
                canonical_label="Python",
                aliases=("Python",),
                families=(JobFamily.BACKEND,),
                occurrences=66,
            ),
            ReferenceSkill(
                skill_id="kubernetes",
                canonical_label="Kubernetes",
                aliases=("Kubernetes", "K8s"),
                families=(JobFamily.DEVOPS,),
                occurrences=26,
            ),
            ReferenceSkill(
                skill_id="kafka",
                canonical_label="Kafka",
                aliases=("Kafka",),
                families=(JobFamily.BACKEND,),
                occurrences=8,
            ),
            ReferenceSkill(
                skill_id="go",
                canonical_label="Go",
                aliases=("Go", "Golang"),
                families=(JobFamily.BACKEND,),
                occurrences=4,
            ),
        ]
    )


def test_sidecar_skills_split_mandatory_then_preferred() -> None:
    raw = RawOffer(source_id="o1", title="Senior Backend Engineer", description="Build APIs.")
    annotation = {
        "family_hint": "backend",
        "experience_level": "Senior",
        "skills_required": '["K8s", "Python", "Golang", "Kafka", "teamwork"]',
    }
    offer = structure_offer(raw, annotation, _index())
    ids = [skill.skill_id for skill in offer.required_skills]
    assert ids[0] == "python"
    assert "kubernetes" in ids
    assert "go" in ids
    mandatory = [
        s.skill_id for s in offer.required_skills if s.requirement is SkillRequirement.MANDATORY
    ]
    preferred = [
        s.skill_id for s in offer.required_skills if s.requirement is SkillRequirement.PREFERRED
    ]
    assert len(mandatory) <= MANDATORY_SKILL_CAP
    assert offer.seniority is SeniorityLevel.SENIOR
    assert "teamwork" not in ids
    assert set(mandatory) | set(preferred) == set(ids)
