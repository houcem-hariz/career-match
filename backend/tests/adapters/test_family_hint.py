"""Family-hint classifier used to curate the corpus."""

from career_match.adapters.ingestion.family_hint import infer_family_hint
from career_match.domain.models.enums import JobFamily


def test_rejects_grocery_front_end_clerk() -> None:
    assert infer_family_hint("Front End Clerk Part Time Evening") is None


def test_rejects_french_grocery_title() -> None:
    assert infer_family_hint("Épicerie Commis temps partiel jour") is None


def test_classifies_explicit_families() -> None:
    assert infer_family_hint("Senior Backend Engineer") is JobFamily.BACKEND
    assert infer_family_hint("Frontend Developer") is JobFamily.FRONTEND
    assert infer_family_hint("Staff Data Engineer") is JobFamily.DATA
    assert infer_family_hint("Senior DevOps Engineer") is JobFamily.DEVOPS
    assert infer_family_hint("Application Security Engineer") is JobFamily.CYBERSECURITY
    assert infer_family_hint("Technical Product Manager") is JobFamily.TECHNICAL_PRODUCT


def test_does_not_label_from_skills_when_title_is_out_of_scope() -> None:
    assert infer_family_hint("Business Development Executive", '["aws", "security"]') is None
    assert infer_family_hint("Solutions Architect (Enterprise Applications)", '["cyber"]') is None


def test_software_engineer_falls_back_to_backend() -> None:
    assert infer_family_hint("Software Engineer") is JobFamily.BACKEND


def test_software_engineer_uses_frontend_skills_when_title_is_generic() -> None:
    assert infer_family_hint("Software Engineer", '["react", "css", "html"]') is JobFamily.FRONTEND
    # Cloud skills on a generic software title must not leak into devops.
    assert (
        infer_family_hint("Software Engineer", '["kubernetes", "terraform", "aws"]')
        is JobFamily.BACKEND
    )
