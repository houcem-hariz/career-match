"""Assign a job-family hint from a title and optional skill list.

Used only during corpus curation, never by the scoring. The hint is a filter so that
the 120-offer subset actually covers the six families; the extraction pipeline will
re-infer the family later from the text.
"""

from __future__ import annotations

import re

from career_match.domain.models.enums import JobFamily

_NON_TECH = re.compile(
    r"cashier|shopper|grocery|deli|produce|\bclerk\b|barista|waiter|nurse|\brn\b|"
    r"warehouse|forklift|material\s+handler|truck\s+driver|cleaner|janitor|"
    r"receptionist|hostess|retail\s+associate|correctional|patient\s+services|"
    r"medicaid|personal\s+shopper|kitchen|dishwasher",
    re.IGNORECASE,
)

_FRENCHISH = re.compile(
    r"\b(commis|épicerie|epicerie|temps\s+partiel|caissier|magasinier|vendeur)\b",
    re.IGNORECASE,
)

_CYBER = re.compile(
    r"\bcyber|infosec|appsec|pentes|penetration\s+test|security\s+engineer|"
    r"security\s+analyst|soc\s+analyst|application\s+security|cloud\s+security|"
    r"security\s+architect|information\s+security|devsecops",
    re.IGNORECASE,
)

_DEVOPS = re.compile(
    r"\bdevops\b|site\s+reliability|\bsre\b|platform\s+engineer|cloud\s+engineer|"
    r"infrastructure\s+engineer|reliability\s+engineer|\bkubernetes\b|\bterraform\b",
    re.IGNORECASE,
)

_DATA = re.compile(
    r"data\s+scientist|data\s+engineer|data\s+analyst|machine\s+learning|"
    r"\bml\s+engineer\b|analytics\s+engineer|\bbi\s+engineer\b|research\s+scientist|"
    r"data\s+platform|mlops",
    re.IGNORECASE,
)

_FRONTEND = re.compile(
    r"front[\s-]?end\s+(engineer|developer|dev)\b|frontend\s+(engineer|developer)|"
    r"react\s+developer|angular\s+developer|vue(?:\.js)?\s+developer|"
    r"ui\s+engineer|javascript\s+engineer",
    re.IGNORECASE,
)

_BACKEND = re.compile(
    r"back[\s-]?end\s+(engineer|developer|dev)\b|backend\s+(engineer|developer)|"
    r"java\s+(engineer|developer)|python\s+(engineer|developer)|"
    r"golang\s+(engineer|developer)|\bgo\s+engineer\b|"
    r"node(?:\.js)?\s+(engineer|developer)|api\s+engineer|"
    r"\.net\s+(engineer|developer)|django|spring\s+boot",
    re.IGNORECASE,
)

_PRODUCT = re.compile(
    r"product\s+manager|technical\s+product|engineering\s+manager|"
    r"product\s+owner|technical\s+program\s+manager|\btpm\b",
    re.IGNORECASE,
)

_SOFTWARE = re.compile(
    r"software\s+(engineer|developer)|full[\s-]?stack|programmer",
    re.IGNORECASE,
)

_SKILL_FRONTEND = re.compile(r"\b(react|angular|vue|next\.js|css|html)\b", re.IGNORECASE)
_SKILL_BACKEND = re.compile(
    r"\b(java|python|golang|\bgo\b|node|\.net|django|spring|postgresql|sql)\b",
    re.IGNORECASE,
)


_OFF_SCOPE = re.compile(
    r"business\s+development|account\s+executive|\bsales\b|wealth\s+management|"
    r"electrical|solutions\s+architect|overnight\s+shift",
    re.IGNORECASE,
)


def infer_family_hint(title: str, skills_blob: str = "") -> JobFamily | None:
    """Return a family hint, or None when the posting is not in scope.

    Specific families are decided from the title only. Skills are consulted solely
    to disambiguate generic "software engineer" titles, otherwise a mention of AWS
    in a sales posting would be labelled devops.
    """
    if not title or _NON_TECH.search(title) or _FRENCHISH.search(title) or _OFF_SCOPE.search(title):
        return None

    if _CYBER.search(title):
        return JobFamily.CYBERSECURITY
    if _DEVOPS.search(title):
        return JobFamily.DEVOPS
    if _DATA.search(title):
        return JobFamily.DATA
    if _FRONTEND.search(title):
        return JobFamily.FRONTEND
    if _BACKEND.search(title):
        return JobFamily.BACKEND
    if _PRODUCT.search(title):
        return JobFamily.TECHNICAL_PRODUCT

    if _SOFTWARE.search(title):
        if _SKILL_FRONTEND.search(skills_blob) and not _SKILL_BACKEND.search(skills_blob):
            return JobFamily.FRONTEND
        return JobFamily.BACKEND

    return None
