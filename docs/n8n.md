# n8n (semaine 7)

n8n **orchestre**, il ne calcule pas de score. Le workflow appelle `POST /api/match` et compte les paniers renvoyés par l’API.

## Prérequis

1. API allumée : depuis `backend/`, `uv run python -m career_match.cli.serve`
2. n8n en local (Docker ou desktop) sur la même machine

Si n8n tourne dans Docker, l’URL du workflow utilise `host.docker.internal:8000`. En process local : remplacer par `http://127.0.0.1:8000/api/match?k=10`.

## Importer

1. n8n → *Workflows* → *Import from File*
2. Choisir [n8n/jane-match.json](n8n/jane-match.json)
3. *Test workflow*

Le nœud **Count buckets** affiche `eligible` / `reachable` / `out_of_reach` plus le titre de la première carte. Aucun chiffre n’est inventé dans n8n.
