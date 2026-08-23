"""Deterministic referential construction from skill mentions."""

from career_match.domain.models.enums import JobFamily
from career_match.domain.normalization.referential import build_referential, skill_id_for


def test_aliases_collapse_to_one_id() -> None:
    assert skill_id_for("React.js") == "react"
    assert skill_id_for("ReactJS") == "react"
    assert skill_id_for("K8s") == "kubernetes"
    assert skill_id_for("Node.js") == "nodejs"
    assert skill_id_for("PostgreSQL") == "postgresql"
    assert skill_id_for("postgres") == "postgresql"
    assert skill_id_for("CI/CD") == "cicd"
    assert skill_id_for("Golang") == "go"


def test_soft_skills_are_dropped() -> None:
    assert skill_id_for("communication") is None
    assert skill_id_for("Team player") is None
    assert skill_id_for("Bachelor's degree") is None


def test_build_referential_merges_and_counts() -> None:
    skills = build_referential(
        [
            ("React.js", JobFamily.FRONTEND),
            ("ReactJS", JobFamily.FRONTEND),
            ("Kubernetes", JobFamily.DEVOPS),
            ("K8s", JobFamily.DEVOPS),
            ("communication", JobFamily.BACKEND),
        ]
    )
    by_id = {skill.skill_id: skill for skill in skills}
    assert set(by_id) == {"react", "kubernetes"}
    assert by_id["react"].occurrences == 2
    assert "React.js" in by_id["react"].aliases
    assert JobFamily.FRONTEND in by_id["react"].families
    assert by_id["kubernetes"].canonical_label == "Kubernetes"


def test_min_occurrences_filters_rare_skills() -> None:
    skills = build_referential(
        [
            ("Python", JobFamily.BACKEND),
            ("Python", JobFamily.DATA),
            ("ObscureLib", JobFamily.BACKEND),
        ],
        min_occurrences=2,
    )
    assert [skill.skill_id for skill in skills] == ["python"]
