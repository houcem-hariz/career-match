# API HTTP

Contrat **OpenAPI** généré par FastAPI. Ne pas dupliquer les champs ici.

1. `docker compose up -d` puis depuis `backend/` : `uv run python -m career_match.cli.serve`
2. Swagger (essayer) : http://127.0.0.1:8000/docs
3. ReDoc (lire) : http://127.0.0.1:8000/redoc
4. Spécification : http://127.0.0.1:8000/openapi.json

`POST /api/match` : exactement une entrée parmi JSON `text` (mini-CV), JSON `example` (`jane_doe_backend`), ou fichier PDF `cv`. Même cartes que `run_pipeline`.
