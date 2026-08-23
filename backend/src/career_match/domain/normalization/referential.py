"""Build the skill referential from corpus mentions. Pure: no I/O, no LLM."""

from __future__ import annotations

import re
from collections import Counter

from career_match.domain.models.enums import JobFamily
from career_match.domain.models.skill import ReferenceSkill

_NON_ALNUM = re.compile(r"[^a-z0-9+]+")

# Surface forms that must collapse to one id. Keys are already slugified.
_CANONICAL_IDS: dict[str, str] = {
    "reactjs": "react",
    "react_js": "react",
    "k8s": "kubernetes",
    "nodejs": "nodejs",
    "node_js": "nodejs",
    "node": "nodejs",
    "postgres": "postgresql",
    "psql": "postgresql",
    "js": "javascript",
    "ts": "typescript",
    "gcp": "gcp",
    "google_cloud": "gcp",
    "google_cloud_platform": "gcp",
    "amazon_web_services": "aws",
    "ms_azure": "azure",
    "ci_cd": "cicd",
    "cicd": "cicd",
    "ml": "machine_learning",
    "machinelearning": "machine_learning",
    "ai_ml": "machine_learning",
    "tf": "tensorflow",
    "py": "python",
    "golang": "go",
    "golang_go": "go",
    "cpp": "cpp",
    "c++": "cpp",
    "csharp": "csharp",
    "c#": "csharp",
    "dotnet": "dotnet",
    "net": "dotnet",
    "nextjs": "nextjs",
    "next_js": "nextjs",
    "vuejs": "vue",
    "vue_js": "vue",
    "postgres_sql": "postgresql",
    "rest_api": "rest",
    "restful_apis": "rest",
    "restful_api": "rest",
    "k8": "kubernetes",
}

_CANONICAL_LABELS: dict[str, str] = {
    "react": "React",
    "kubernetes": "Kubernetes",
    "nodejs": "Node.js",
    "postgresql": "PostgreSQL",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "gcp": "GCP",
    "aws": "AWS",
    "azure": "Azure",
    "cicd": "CI/CD",
    "machine_learning": "Machine Learning",
    "python": "Python",
    "go": "Go",
    "cpp": "C++",
    "csharp": "C#",
    "dotnet": ".NET",
    "nextjs": "Next.js",
    "vue": "Vue",
    "rest": "REST",
}

# Soft skills and posting boilerplate that must not enter the referential.
_NOISE = {
    "communication",
    "teamwork",
    "collaboration",
    "leadership",
    "mentoring",
    "mentorship",
    "stakeholder_management",
    "problem_solving",
    "problem_solving_skills",
    "analytical_skills",
    "attention_to_detail",
    "self_motivated",
    "fast_paced",
    "english",
    "bachelor",
    "bachelors_degree",
    "masters_degree",
    "degree",
    "computer_science",
    "software_engineering",
    "software_development",
    "programming",
    "coding",
    "documentation",
    "presentation",
    "hiring",
    "coaching",
    "time_management",
    "organizational",
    "organisational",
    "written_communication",
    "verbal_communication",
    "interpersonal_skills",
    "team_player",
    "passion",
    "ownership",
    "cross_functional",
    "cross_functional_collaboration",
    "cloud",
    "software",
    "engineering",
    "technical_skills",
}


def slugify(label: str) -> str:
    text = label.strip().lower().replace("'", "").replace("\u2019", "")
    text = text.replace(".js", "js").replace("c++", "cpp").replace("c#", "csharp")
    text = text.replace("+", "plus")
    slug = _NON_ALNUM.sub("_", text).strip("_")
    return slug


def skill_id_for(label: str) -> str | None:
    """Return a stable id, or None when the label is noise or empty."""
    slug = slugify(label)
    if len(slug) < 2 or len(slug) > 40 or slug in _NOISE or slug.isdigit():
        return None
    return _CANONICAL_IDS.get(slug, slug)


def build_referential(
    mentions: list[tuple[str, JobFamily | None]],
    min_occurrences: int = 1,
) -> list[ReferenceSkill]:
    """Group surface forms into ``ReferenceSkill`` rows.

    ``mentions`` is (raw_label, family_or_none) as extracted from the corpus.
    """
    grouped: dict[str, dict[str, object]] = {}
    for label, family in mentions:
        skill_id = skill_id_for(label)
        if skill_id is None:
            continue
        bucket = grouped.setdefault(
            skill_id,
            {
                "labels": Counter(),
                "families": set(),
                "offers": 0,
            },
        )
        labels = bucket["labels"]
        families = bucket["families"]
        assert isinstance(labels, Counter)
        assert isinstance(families, set)
        labels[label.strip()] += 1
        if family is not None:
            families.add(family)

    skills: list[ReferenceSkill] = []
    for skill_id, bucket in grouped.items():
        labels = bucket["labels"]
        families = bucket["families"]
        assert isinstance(labels, Counter)
        assert isinstance(families, set)
        occurrences = sum(labels.values())
        if occurrences < min_occurrences:
            continue
        canonical = _CANONICAL_LABELS.get(skill_id) or labels.most_common(1)[0][0]
        aliases = tuple(sorted({canonical, *labels.keys()}, key=str.lower))
        skills.append(
            ReferenceSkill(
                skill_id=skill_id,
                canonical_label=canonical,
                aliases=aliases,
                families=tuple(sorted(families, key=lambda item: item.value)),
                occurrences=sum(labels.values()),
            )
        )
    return sorted(skills, key=lambda skill: (-skill.occurrences, skill.skill_id))
