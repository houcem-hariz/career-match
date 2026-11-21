# Script de démo (semaine 8)

Oral **8–10 minutes**. Une histoire : le score est **déjà calculé** ; l’UI, le chat et n8n ne font que le montrer.

Toujours **`http://localhost:3000`** (jamais mélangé avec `127.0.0.1` : le cookie `cm_session` disparaît).

## Avant d’entrer

```bash
docker compose up -d
cd backend
uv run python -m career_match.cli.serve
```

Front : `cd frontend` puis `npm run dev` → `http://localhost:3000`.

Si le chat Groq refuse les tool calls : `LLM_PROVIDER=openai` dans `.env` et relancer l’API.

## Scène 1 — Invité, pas de paywall (~1 min 30)

Accueil `/`. Dire : *on n’est pas un moteur de recherche d’offres ; le texte est un mini-CV.*

Chip **Jane Doe** → `/offers`.

Montrer les **trois paniers** (même vides). Phrase : *on ne jette aucune offre ; on range.*

## Scène 2 — La fiche, le cœur de l’oral (~2 min 30)

Cliquer une carte **reachable** ou **out_of_reach** (plus parlant qu’un eligible parfait).

Montrer, dans cet ordre :

1. score /100 et panier
2. six barres (`mandatory_skills` … `semantic`)
3. un ou deux **gaps** (mandatory)
4. une **simulation** : score avant → après, panier avant → après

Phrase : *ces chiffres viennent du domain ; FastAPI ne les recalcule pas.*

## Scène 3 — Corriger sans rescoring auto (~1 min 30)

**Profile** → changer une compétence (enlever kubernetes, ou le niveau).

**Save** : les offres **ne bougent pas**. Dire : *PUT ne relance pas le graphe.*

**Recalculer** → retour liste. Montrer qu’une carte a changé de panier ou de score.

**New profile** seulement si on te demande un second match : ça ramène à `/`.

## Scène 4 — Essayer puis sauver (~1 min)

**Sign in / Create account** (email + mot de passe ≥ 8). Dire : *le compte ne sert qu’à garder le Profile, pas à débloquer le match.*

F5 sur `/offers` ou `/profile` : encore là (session). Mentionner : *redémarrer l’API vide la RAM ; un login rehydrate depuis `data/cache/accounts.json`.*

Ne pas perdre de temps sur « forgot password » (il n’existe pas).

## Scène 5 — Chat agent (~1 min 30)

Sur la **fiche** : Chat → suggestion **Why is this offer … ?**

Sur la **liste** : **Which course helps most?**

Phrase : *le LLM n’invente pas le 0–100 ; `tools_used` (Swagger) montre list_matched_offers / simulate_catalogue_course.*

Si la réponse est vide ou hallucinée : ouvrir `/docs`, `POST /api/chat`, montrer `tools_used`. Ce n’est pas un échec de démo, c’est le contrat.

## Si le temps reste (~1 min)

Au choix, **un seul** :

- Terminal : `uv run python -m career_match.cli.eval_cases` → *12 cas, 12 ok. Seconde passe : reachable jusqu’à 3 mandatory.*
- n8n : importer `docs/n8n/jane-match.json` → Test → *n8n compte les paniers, il ne score pas.*

## Ce qu’on ne montre pas

OCR, Google login, streaming, historique long, Redis. Dire *hors périmètre, journal v2* si on te le demande.

## Filet

| Ça casse | Que dire / faire |
|---|---|
| `/offers` 404 | cookie : rester sur localhost |
| Match lent | cache extraction ; deuxième clic Jane est plus court |
| Chat muet | Swagger + `tools_used` ; basculer OpenAI |
| Postgres down | `docker compose up -d` puis relancer `serve` |
