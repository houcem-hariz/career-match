"""Shared vocabulary between profiles and offers.

Every scale used on both sides of the matching is defined here exactly once. This is what
makes the offer schema a true mirror of the profile schema: without a shared vocabulary the
scoring cannot be expressed.

Ordinal scales derive from IntEnum on purpose, so that scoring can compare and subtract
levels directly instead of going through a lookup table.
"""

from enum import IntEnum, StrEnum


class JobFamily(StrEnum):
    BACKEND = "backend"
    FRONTEND = "frontend"
    DATA = "data"
    DEVOPS = "devops"
    CYBERSECURITY = "cybersecurity"
    TECHNICAL_PRODUCT = "technical_product"


class SkillLevel(IntEnum):
    """Ordinal 1-4 scale.

    The wording of each level is injected verbatim into the extraction prompt: a model asked
    to pick between defined labels is far more stable than one asked for a number.

    AWARENESS  - has been exposed to it, cannot work unsupervised
    WORKING    - delivers standard tasks unsupervised
    PROFICIENT - handles complex cases, makes design decisions
    EXPERT     - reference on the subject, mentors others
    """

    AWARENESS = 1
    WORKING = 2
    PROFICIENT = 3
    EXPERT = 4


class SeniorityLevel(IntEnum):
    """Ordinal so that the seniority gap can be signed.

    A negative gap (candidate below the offer) and a positive one (candidate above) are not
    penalised the same way. See the scoring module.
    """

    JUNIOR = 1
    MID = 2
    SENIOR = 3
    LEAD = 4


class EducationLevel(IntEnum):
    NONE = 0
    HIGH_SCHOOL = 1
    BACHELOR = 2
    MASTER = 3
    DOCTORATE = 4


class LanguageProficiency(IntEnum):
    """CEFR scale, kept ordinal to allow threshold comparisons."""

    A1 = 1
    A2 = 2
    B1 = 3
    B2 = 4
    C1 = 5
    C2 = 6


class ContractType(StrEnum):
    PERMANENT = "permanent"
    FIXED_TERM = "fixed_term"
    INTERNSHIP = "internship"
    APPRENTICESHIP = "apprenticeship"
    FREELANCE = "freelance"


class WorkModel(StrEnum):
    ONSITE = "onsite"
    HYBRID = "hybrid"
    REMOTE = "remote"


class SkillSource(StrEnum):
    """Traceability of every skill carried by a profile.

    Enables the human correction rate to be measured, which is used as a quality metric for
    the extraction step.
    """

    CV_EXTRACTION = "cv_extraction"
    USER_INPUT = "user_input"
    INFERRED = "inferred"


class SkillRequirement(StrEnum):
    """Offer side only. Drives the bucket assignment: a missing mandatory skill downgrades
    the offer, a missing preferred one only costs a few points."""

    MANDATORY = "mandatory"
    PREFERRED = "preferred"


class MatchBucket(StrEnum):
    """Offers are ranked, never silently dropped: the reachable bucket is precisely what the
    gap analysis and the impact simulation exist to serve."""

    ELIGIBLE = "eligible"
    REACHABLE = "reachable"
    OUT_OF_REACH = "out_of_reach"
