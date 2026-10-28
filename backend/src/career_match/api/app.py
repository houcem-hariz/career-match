"""FastAPI app factory. Tests inject PipelineDeps; the CLI builds live deps."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.datastructures import UploadFile

from career_match.adapters.llm.factory import build_chat_llm
from career_match.api.accounts import (
    Account,
    AccountStore,
    AuthError,
    InMemoryAccountStore,
    JsonAccountStore,
    authenticate,
)
from career_match.api.chat import ChatClient, LangchainChatClient, run_session_chat
from career_match.api.match import (
    HttpMatchResult,
    MatchRequestError,
    run_match,
    run_match_from_profile,
)
from career_match.api.openapi import API_DESCRIPTION, MATCH_REQUEST_BODY, install_openapi
from career_match.api.schemas import (
    AuthCredentials,
    CardPayload,
    ChatRequest,
    ChatResponse,
    ErrorBody,
    MatchResponse,
    MeResponse,
)
from career_match.api.session import COOKIE_NAME, GuestSession, NotFoundError, SessionStore
from career_match.domain.models.profile import Profile
from career_match.pipeline.deps import PipelineDeps
from career_match.pipeline.runtime import build_live_deps, default_data_paths
from career_match.settings import Settings, get_settings, project_root

_CORS_ORIGINS = (
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
)


def create_app(
    deps: PipelineDeps,
    *,
    examples: dict[str, Path] | None = None,
    store: SessionStore | None = None,
    accounts: AccountStore | None = None,
    chat_client: ChatClient | None = None,
) -> FastAPI:
    app = FastAPI(title="career-match", version="0.1.0", description=API_DESCRIPTION)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(_CORS_ORIGINS),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.deps = deps
    app.state.examples = examples or {}
    app.state.store = store or SessionStore()
    app.state.accounts = accounts or InMemoryAccountStore()
    app.state.chat_client = chat_client

    @app.exception_handler(MatchRequestError)
    async def _match_request_error(_request: Request, exc: MatchRequestError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(NotFoundError)
    async def _not_found_error(_request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(AuthError)
    async def _auth_error(_request: Request, exc: AuthError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

    @app.post(
        "/api/match",
        response_model=MatchResponse,
        responses={400: {"model": ErrorBody, "description": "Missing, extra, or unknown source"}},
        tags=["matching"],
        summary="Score offers against a profile",
        description=(
            "Send exactly one source: JSON `text`, JSON `example` (`jane_doe_backend`), "
            "or multipart `cv` (PDF). Stores cards in a guest cookie session. "
            "No login required. If the session is logged in, the account snapshot is updated."
        ),
        openapi_extra={"requestBody": MATCH_REQUEST_BODY},
    )
    async def match(
        request: Request,
        response: Response,
        k: int = Query(10, ge=1, le=120, description="Top-k after filters"),
    ) -> MatchResponse:
        pdf_bytes, text, example, body_k = await _read_body(request)
        result = run_match(
            cast(PipelineDeps, request.app.state.deps),
            k=body_k if body_k is not None else k,
            pdf_bytes=pdf_bytes,
            text=text,
            example=example,
            examples=cast(dict[str, Path], request.app.state.examples),
        )
        _save_match(request, response, result)
        return MatchResponse.model_validate(result.as_payload())

    @app.get(
        "/api/offers",
        response_model=MatchResponse,
        responses={404: {"model": ErrorBody, "description": "No match stored for this session"}},
        tags=["matching"],
        summary="List scored cards from the session",
    )
    async def list_offers(request: Request) -> MatchResponse:
        store_ = cast(SessionStore, request.app.state.store)
        return store_.require_cards(request.cookies.get(COOKIE_NAME)).to_match_response()

    @app.get(
        "/api/offers/{source_id}",
        response_model=CardPayload,
        responses={404: {"model": ErrorBody, "description": "No session or unknown source_id"}},
        tags=["matching"],
        summary="One scored card from the session",
    )
    async def get_offer(source_id: str, request: Request) -> CardPayload:
        store_ = cast(SessionStore, request.app.state.store)
        return store_.require_cards(request.cookies.get(COOKIE_NAME)).card(source_id)

    @app.get(
        "/api/profile",
        response_model=Profile,
        responses={404: {"model": ErrorBody, "description": "No profile in this session"}},
        tags=["profile"],
        summary="Read the session Profile",
    )
    async def get_profile(request: Request) -> Profile:
        store_ = cast(SessionStore, request.app.state.store)
        session = store_.require_profile(request.cookies.get(COOKIE_NAME))
        assert session.profile is not None
        return session.profile

    @app.put(
        "/api/profile",
        response_model=Profile,
        responses={404: {"model": ErrorBody, "description": "No session"}},
        tags=["profile"],
        summary="Replace the session Profile without rescoring",
        description=(
            "Full Profile body. Sets `user_edited` and increments `correction_count`. "
            "Does not run the scorer; call POST /api/rematch afterwards."
        ),
    )
    async def put_profile(payload: Profile, request: Request) -> Profile:
        store_ = cast(SessionStore, request.app.state.store)
        session_id = request.cookies.get(COOKIE_NAME)
        session = store_.require(session_id)
        previous = session.profile
        session.profile = payload.model_copy(
            update={
                "user_edited": True,
                "correction_count": (
                    previous.correction_count if previous is not None else payload.correction_count
                )
                + 1,
                "profile_id": previous.profile_id if previous is not None else payload.profile_id,
            }
        )
        assert session_id is not None
        store_.put(session_id, session)
        _persist_account(request, session)
        return session.profile

    @app.post(
        "/api/rematch",
        response_model=MatchResponse,
        responses={404: {"model": ErrorBody, "description": "No profile in this session"}},
        tags=["matching"],
        summary="Rescore the stored Profile",
        description=(
            "Writes a temp profile.json and re-enters the graph "
            "(no extract, no normalize)."
        ),
    )
    async def rematch(
        request: Request,
        response: Response,
        k: int = Query(10, ge=1, le=120, description="Top-k after filters"),
    ) -> MatchResponse:
        store_ = cast(SessionStore, request.app.state.store)
        session = store_.require_profile(request.cookies.get(COOKIE_NAME))
        assert session.profile is not None
        result = run_match_from_profile(
            cast(PipelineDeps, request.app.state.deps),
            session.profile,
            k=k,
        )
        _save_match(request, response, result)
        return MatchResponse.model_validate(result.as_payload())

    @app.post(
        "/api/auth/register",
        response_model=MeResponse,
        status_code=201,
        responses={
            400: {"model": ErrorBody, "description": "Invalid email or short password"},
            409: {"model": ErrorBody, "description": "Email already registered"},
        },
        tags=["auth"],
        summary="Create an account and attach the guest Profile",
    )
    async def register(body: AuthCredentials, request: Request, response: Response) -> MeResponse:
        accounts_ = cast(AccountStore, request.app.state.accounts)
        account = accounts_.create(body.email, body.password)
        return _bind_account(request, response, account)

    @app.post(
        "/api/auth/login",
        response_model=MeResponse,
        responses={
            400: {"model": ErrorBody, "description": "Invalid email"},
            401: {"model": ErrorBody, "description": "Unknown email or bad password"},
        },
        tags=["auth"],
        summary="Log in and attach or hydrate the Profile",
    )
    async def login(body: AuthCredentials, request: Request, response: Response) -> MeResponse:
        accounts_ = cast(AccountStore, request.app.state.accounts)
        account = authenticate(accounts_, body.email, body.password)
        return _bind_account(request, response, account)

    @app.post(
        "/api/auth/logout",
        status_code=204,
        tags=["auth"],
        summary="Clear the account link; keep the guest cards",
    )
    async def logout(request: Request) -> Response:
        store_ = cast(SessionStore, request.app.state.store)
        session_id = request.cookies.get(COOKIE_NAME)
        session = store_.get(session_id)
        if session is not None and session_id is not None:
            session.user_id = None
            store_.put(session_id, session)
        return Response(status_code=204)

    @app.get(
        "/api/auth/me",
        response_model=MeResponse,
        tags=["auth"],
        summary="Who the session cookie is bound to",
    )
    async def me(request: Request) -> MeResponse:
        store_ = cast(SessionStore, request.app.state.store)
        accounts_ = cast(AccountStore, request.app.state.accounts)
        session = store_.get(request.cookies.get(COOKIE_NAME))
        if session is None or session.user_id is None:
            return MeResponse(authenticated=False)
        account = accounts_.get_by_id(session.user_id)
        if account is None:
            return MeResponse(authenticated=False)
        return MeResponse(authenticated=True, email=account.email)

    @app.post(
        "/api/chat",
        response_model=ChatResponse,
        responses={
            400: {"model": ErrorBody, "description": "Empty message"},
            404: {"model": ErrorBody, "description": "No match in this session"},
            503: {"model": ErrorBody, "description": "Chat model is not configured"},
        },
        tags=["chat"],
        summary="Ask about the current match",
        description=(
            "Agent over the session cards. It calls the same simulate_course / card "
            "payloads as MCP. It does not compute a new score."
        ),
    )
    async def chat(body: ChatRequest, request: Request) -> ChatResponse:
        message = body.message.strip()
        if not message:
            raise HTTPException(status_code=400, detail="message is required.")
        client = cast(ChatClient | None, getattr(request.app.state, "chat_client", None))
        if client is None:
            raise HTTPException(status_code=503, detail="Chat model is not configured.")
        store_ = cast(SessionStore, request.app.state.store)
        session = store_.require_cards(request.cookies.get(COOKIE_NAME))
        outcome = run_session_chat(
            cast(PipelineDeps, request.app.state.deps),
            session,
            message=message,
            source_id=body.source_id,
            client=client,
        )
        return ChatResponse(reply=outcome.reply, tools_used=outcome.tools_used)

    install_openapi(app)
    return app


def _save_match(request: Request, response: Response, result: HttpMatchResult) -> None:
    store = cast(SessionStore, request.app.state.store)
    session_id = request.cookies.get(COOKIE_NAME) or store.new_id()
    existing = store.get(session_id)
    session = GuestSession(
        candidate_count=result.candidate_count,
        query_from_cache=result.query_from_cache,
        cards=[CardPayload.model_validate(card) for card in result.cards],
        profile=result.profile,
        user_id=existing.user_id if existing is not None else None,
    )
    store.put(session_id, session)
    _persist_account(request, session)
    _set_session_cookie(response, session_id)


def _bind_account(request: Request, response: Response, account: Account) -> MeResponse:
    """In-memory Profile wins; otherwise hydrate from the account snapshot."""
    session_id, session = _session_or_create(request, response)
    session.user_id = account.user_id
    if session.profile is None:
        session.profile = account.profile
        session.cards = list(account.cards)
        session.candidate_count = account.candidate_count
        session.query_from_cache = account.query_from_cache
    cast(SessionStore, request.app.state.store).put(session_id, session)
    _persist_account(request, session)
    return MeResponse(authenticated=True, email=account.email)


def _session_or_create(request: Request, response: Response) -> tuple[str, GuestSession]:
    store = cast(SessionStore, request.app.state.store)
    session_id = request.cookies.get(COOKIE_NAME)
    session = store.get(session_id)
    if session is not None and session_id is not None:
        return session_id, session
    session_id = store.new_id()
    session = GuestSession(candidate_count=0, query_from_cache=False, cards=[])
    store.put(session_id, session)
    _set_session_cookie(response, session_id)
    return session_id, session


def _persist_account(request: Request, session: GuestSession) -> None:
    if session.user_id is None:
        return
    accounts = cast(AccountStore, request.app.state.accounts)
    account = accounts.get_by_id(session.user_id)
    if account is None:
        return
    account.profile = session.profile
    account.cards = list(session.cards)
    account.candidate_count = session.candidate_count
    account.query_from_cache = session.query_from_cache
    accounts.put(account)


def _set_session_cookie(response: Response, session_id: str) -> None:
    response.set_cookie(
        COOKIE_NAME,
        session_id,
        httponly=True,
        samesite="lax",
        max_age=86400,
        path="/",
    )


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
    accounts_path = project_root() / "data" / "cache" / "accounts.json"
    return create_app(
        deps,
        examples=examples,
        accounts=JsonAccountStore(accounts_path),
        chat_client=LangchainChatClient(build_chat_llm(settings)),
    )
