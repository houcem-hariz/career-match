"""Match buckets: offers are ranked, never silently dropped."""

from career_match.domain.models.enums import MatchBucket
from career_match.domain.scoring.config import ScoringConfig


def assign_bucket(
    *,
    mandatory_gap_count: int,
    seniority_gap: int,
    config: ScoringConfig,
) -> MatchBucket:
    if seniority_gap <= config.out_of_reach_seniority_gap:
        return MatchBucket.OUT_OF_REACH
    if mandatory_gap_count == 0 and seniority_gap >= config.min_seniority_gap_eligible:
        return MatchBucket.ELIGIBLE
    if (
        mandatory_gap_count <= config.max_mandatory_gaps_reachable
        and seniority_gap >= config.min_seniority_gap_reachable
    ):
        return MatchBucket.REACHABLE
    return MatchBucket.OUT_OF_REACH


BUCKET_RANK = {
    MatchBucket.ELIGIBLE: 0,
    MatchBucket.REACHABLE: 1,
    MatchBucket.OUT_OF_REACH: 2,
}
