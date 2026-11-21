"""Gold buckets vs score_offer. Uses the committed corpus, not fakes."""

from __future__ import annotations

from career_match.adapters.matching.config_io import load_scoring_config
from career_match.domain.models.enums import MatchBucket
from career_match.domain.scoring.config import DEFAULT_SCORING_CONFIG
from career_match.domain.scoring.score import score_offer
from career_match.eval.annotated import evaluate_cases, load_corpus_offers, load_profiles
from career_match.settings import project_root


def test_all_annotated_cases_match_scoring_json() -> None:
    results = evaluate_cases()
    assert len(results) >= 12
    mismatches = [
        (
            item.case.case_id,
            item.case.expected_bucket.value,
            item.predicted.value,
        )
        for item in results
        if not item.ok
    ]
    assert mismatches == []


def test_second_pass_opens_three_mandatory_gaps() -> None:
    """Week-3 default (max 2) was too strict on sidecar-heavy backend offers."""
    root = project_root()
    jane = load_profiles(root / "data" / "eval" / "profiles")["jane_backend"]
    offer = load_corpus_offers(root)["nextgig-bd2c5fe13dad"]
    live = load_scoring_config(root / "data" / "processed" / "scoring.json")
    before = score_offer(jane, offer, 0.5, DEFAULT_SCORING_CONFIG)
    after = score_offer(jane, offer, 0.5, live)
    assert before.mandatory_gap_count == 3
    assert before.bucket is MatchBucket.OUT_OF_REACH
    assert after.bucket is MatchBucket.REACHABLE
    assert live.max_mandatory_gaps_reachable == 3
