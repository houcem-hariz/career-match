"""FastAPI app factory. Tests inject PipelineDeps; the CLI builds live deps."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.datastructures import UploadFile

from career_match.api.match import MatchRequestError, run_match
from career_match.pipeline.deps import PipelineDeps
from career_match.pipeline.runtime import build_live_deps, default_data_paths
from career_match.settings import Settings, get_settings, project_root


def create_app(
    deps: PipelineDeps,
    *,
    examples: dict[str, Path] | None = None,
) -> FastAPI:
    app = FastAPI(title="career-match", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.deps = deps
    app.state.examples = examples or {}

    @app.exception_handler(MatchRequestError)
    async def _match_request_error(_request: Request, exc: MatchRequestError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.post("/api/match")
    async def match(
        request: Request,
        k: int = Query(10, ge=1, le=120),
    ) -> dict[str, Any]:
        pdf_bytes, text, example, body_k = await _read_body(request)
        return run_match(
            cast(PipelineDeps, request.app.state.deps),
            k=body_k if body_k is not None else k,
            pdf_bytes=pdf_bytes,
            text=text,
            example=example,
            examples=cast(dict[str, Path], request.app.state.examples),
        )

    return app


async def _read_body(
    request: Request,
) -> tuple[bytes | None, str | None, str | None, int | None]:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        if not isinstance(body, dict):
            raise MatchRequestError("JSON body must be an object.")
        text = body.get("text")
        example = body.get("example")
        raw_k = body.get("k")
        k = raw_k if isinstance(raw_k, int) else None
        return (
            None,
            text if isinstance(text, str) else None,
            example if isinstance(example, str) else None,
            k,
        )
    if (
        "multipart/form-data" in content_type
        or "application/x-www-form-urlencoded" in content_type
    ):
        form = await request.form()
        upload = form.get("cv")
        pdf_bytes: bytes | None = None
        if isinstance(upload, UploadFile) and upload.filename:
            pdf_bytes = await upload.read()
        text = form.get("text")
        example = form.get("example")
        return (
            pdf_bytes,
            text if isinstance(text, str) else None,
            example if isinstance(example, str) else None,
            None,
        )
    return None, None, None, None


def create_live_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    paths = default_data_paths()
    deps = build_live_deps(
        settings,
        referential_path=paths["referential"],
        scoring_path=paths["scoring"],
        catalogue_path=paths["catalogue"],
    )
    jane = project_root() / "data" / "raw" / "cvs" / "jane_doe_backend.pdf"
    examples = {"jane_doe_backend": jane} if jane.is_file() else {}
    return create_app(deps, examples=examples)
