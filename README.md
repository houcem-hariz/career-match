# career-match

Plateforme de mise en relation entre un profil candidat et des offres d'emploi, avec analyse
des écarts et recommandations de formation. Projet académique de démonstration des notions
d'IA appliquée : LLM, RAG, LangChain, LangGraph, MCP (serveur et client), IA agentique,
abstraction de fournisseur, n8n.

## Chaîne de valeur

1. Dépôt d'un CV PDF, extraction d'un profil structuré, éditable par l'utilisateur
2. Normalisation des compétences vers un référentiel dérivé du corpus
3. Recherche hybride d'offres : filtres déterministes puis similarité sémantique
4. Score décomposé en six dimensions, offres réparties en trois paniers
5. Analyse d'écart dérivée du calcul, recommandations issues d'un catalogue fermé
6. Simulation d'impact : « si j'acquiers cette compétence, mon score passe à »

## Architecture

```
backend/src/career_match/
  domain/        pur : schémas, scoring, normalisation. Aucune dépendance externe.
  adapters/      LLM, embeddings, parsing PDF, stockage, MCP
  pipeline/      orchestration LangGraph
  api/           FastAPI
  cli/           points d'entrée en ligne de commande
```

La règle structurante : `domain/` ne connaît ni LangChain, ni la base de données, ni le
réseau. Un test d'architecture le vérifie automatiquement.

## Démarrage

```bash
cd backend
uv sync --extra dev
uv run pytest
```

## Avancement

- [ ] Semaine 1 : schémas pivot, extraction CV, corpus brut, référentiel
- [ ] Semaine 2 : normalisation, indexation pgvector, recherche hybride, couche agnostique
- [ ] Semaine 3 : scoring, paniers, écarts, simulation (jalon pivot : chaîne complète en CLI)
- [ ] Semaine 4 : pipeline LangGraph, serveur et client MCP
- [ ] Semaine 5 : API, front, écran offres/détail
- [ ] Semaine 6 : écran profil, chat, agent conversationnel
- [ ] Semaine 7 : n8n, jeu de cas annoté, seconde passe scoring
- [ ] Semaine 8 : rapport, démo

Les décisions de conception et les raccourcis assumés sont consignés dans
[docs/journal.md](docs/journal.md).
