"""Automated enforcement of the layering rule.

The domain layer must depend on nothing but the standard library and Pydantic. This is not a
stylistic preference: it is what keeps the scoring and normalisation logic unit-testable
without a single mock, and therefore what makes the whole test strategy affordable.

Written as a test rather than documented as a convention, because a convention that is not
executed is a convention that erodes.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import career_match.domain

DOMAIN_ROOT = Path(career_match.domain.__file__).parent

# Third-party packages the domain is allowed to know about. Deliberately minimal: Pydantic is
# tolerated because the schemas are the domain, and it carries no I/O.
ALLOWED_THIRD_PARTY = {"pydantic"}


def _imported_roots(source: str) -> set[str]:
    """Return the root package of every import found in a module."""
    roots: set[str] = set()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        # Relative imports stay inside the package, so they need no check.
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def _full_module_targets(source: str) -> set[str]:
    """Return fully qualified module names of `from x.y import z` statements."""
    targets: set[str] = set()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            targets.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                targets.add(alias.name)
    return targets


def _domain_modules() -> list[Path]:
    return sorted(DOMAIN_ROOT.rglob("*.py"))


def test_domain_modules_are_discovered() -> None:
    """Guards against the suite silently passing because it found nothing to inspect."""
    assert _domain_modules(), f"no module found under {DOMAIN_ROOT}"


def test_domain_only_imports_stdlib_and_allowed_third_party() -> None:
    allowed = set(sys.stdlib_module_names) | ALLOWED_THIRD_PARTY | {"career_match"}
    violations: list[str] = []

    for module_path in _domain_modules():
        for root in _imported_roots(module_path.read_text(encoding="utf-8")):
            if root not in allowed:
                violations.append(f"{module_path.name} imports forbidden package '{root}'")

    assert not violations, "domain purity broken:\n" + "\n".join(violations)


def test_domain_never_reaches_into_other_internal_layers() -> None:
    """`career_match` is allowed, but only its `domain` subpackage."""
    violations: list[str] = []

    for module_path in _domain_modules():
        for target in _full_module_targets(module_path.read_text(encoding="utf-8")):
            if target.startswith("career_match.") and not target.startswith("career_match.domain"):
                violations.append(f"{module_path.name} imports '{target}'")

    assert not violations, "domain reaches outside itself:\n" + "\n".join(violations)
