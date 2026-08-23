"""Pure domain layer.

Depends on nothing but the standard library and Pydantic: no LangChain, no database, no
network. This is what makes the deterministic logic unit-testable without a single mock, and
it is enforced automatically by tests/domain/test_architecture.py.
"""
