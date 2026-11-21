# Jeu de cas annoté (semaine 7)

12 paires profil × offre, avec un **panier d’or** (pas un score cible).

- Profils : `data/eval/profiles/*.json`
- Cas : `data/eval/cases.json`
- Le runner appelle `score_offer` sur le corpus structuré. Pas de Postgres, pas de LLM. Les filtres de retrieval ne s’appliquent pas : on juge la politique de paniers.

```bash
cd backend
uv run python -m career_match.cli.eval_cases
uv run pytest tests/eval
```

La seconde passe (octobre 2026) est dans `data/processed/scoring.json` : `max_mandatory_gaps_reachable` passe de 2 à 3, le poids sémantique de 0,20 à 0,15. Le défaut Python (`DEFAULT_SCORING_CONFIG`) reste la politique semaine 3, pour les tests unitaires.
