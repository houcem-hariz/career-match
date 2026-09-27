"""OpenAPI extras FastAPI cannot infer from the manual Request parser."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from career_match.api.schemas import MatchJsonBody

API_DESCRIPTION = """
HTTP facade over the matching pipeline (`run_matching` + `card_payload`).
The scorer is not reimplemented here.

Interactive docs: [/docs](/docs) (Swagger) and [/redoc](/redoc).

`POST /api/match` accepts **exactly one** source:

- JSON `text` — a mini-CV paragraph
- JSON `example` — `jane_doe_backend`
- multipart `cv` — a text PDF

A guest cookie (`cm_session`) stores the cards. Then:

- `GET /api/offers` — same envelope, no rescore
- `GET /api/offers/{source_id}` — one card
""".strip()

_JSON_EXAMPLES: dict[str, Any] = {
    "mini_cv": {
        "summary": "Paste a mini-CV",
        "value": {
            "text": "Senior backend engineer, Python and Kubernetes, 6 years, remote",
            "k": 10,
        },
    },
    "demo": {
        "summary": "Jane Doe chip",
        "value": {"example": "jane_doe_backend", "k": 10},
    },
}

_MULTIPART_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "cv": {
            "type": "string",
            "format": "binary",
            "description": "Text PDF resume. Scanned CVs are out of scope (no OCR).",
        },
        "text": {"type": "string", "description": "Mini-CV paragraph (alternative to cv)."},
        "example": {
            "type": "string",
            "description": "Demo profile id (alternative to cv).",
            "examples": ["jane_doe_backend"],
        },
    },
}

MATCH_REQUEST_BODY: dict[str, Any] = {
    "required": True,
    "content": {
        "application/json": {
            "schema": {"$ref": "#/components/schemas/MatchJsonBody"},
            "examples": _JSON_EXAMPLES,
        },
        "multipart/form-data": {"schema": _MULTIPART_SCHEMA},
    },
}


def install_openapi(app: FastAPI) -> None:
    def _openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        schemas = schema.setdefault("components", {}).setdefault("schemas", {})
        json_schema = MatchJsonBody.model_json_schema(mode="serialization")
        json_schema.pop("$defs", None)
        schemas["MatchJsonBody"] = json_schema
        schema["servers"] = [
            {"url": "http://127.0.0.1:8000", "description": "Local CLI serve"}
        ]
        app.openapi_schema = schema
        return schema

    app.openapi = _openapi  # type: ignore[method-assign]
