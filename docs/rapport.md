# career-match

**Rapport de projet** — plateforme de mise en relation profil / offres, avec analyse d’écarts et simulation de formation.

Projet académique de 8 semaines. Identifiants et code en anglais ; documentation et rapport en français.

---

## Table des matières

1. [Introduction](#1-introduction)
2. [Problématique et périmètre](#2-problématique-et-périmètre)
3. [Architecture](#3-architecture)
4. [Chaîne de matching](#4-chaîne-de-matching)
5. [Rôles de l’IA](#5-rôles-de-lia)
6. [Application](#6-application)
7. [Évaluation](#7-évaluation)
8. [Démonstration](#8-démonstration)
9. [Limites et perspectives](#9-limites-et-perspectives)
10. [Conclusion](#10-conclusion)

---

## 1. Introduction

Les outils d’emploi grand public rangent souvent les offres derrière une barre de mots-clés (« Dev React Paris »). Le score, quand il existe, est opaque : on ne sait pas si l’on est écarté pour une compétence mandatory, pour la séniorité, ou pour un malentendu sémantique.

**career-match** inverse le point de départ. L’utilisateur dépose **qui il est** (CV PDF, mini-CV, ou un exemple). Le système extrait un profil, le normalise vers un référentiel dérivé du corpus, retrouve des offres par filtres puis similarité, puis **explique** le résultat : six dimensions, trois paniers, écarts, et une simulation « si j’acquiers cette compétence, mon score et mon panier changent ».

Le projet sert aussi de démonstrateur des notions d’IA appliquée visées par le cursus : LLM, RAG hybride, abstraction de fournisseur, LangGraph, MCP, agent conversationnel, n8n. La contrainte structurante, tenue du début à la fin : **aucun modèle ne calcule le score**. L’extraction et les embeddings sont probabilistes ; la normalisation, les filtres, les paniers et la simulation sont déterministes et testables sans mock.

---

## 2. Problématique et périmètre

### 2.1 Question

Comment apparier un profil candidat à un corpus d’offres tech de façon **explicable**, sans laisser un LLM inventer un 0–100, tout en montrant une chaîne complète (extraction → recherche → score → interface → agent) dans un calendrier de 8 × 14 h ?

### 2.2 Chaîne de valeur

1. Dépôt d’un CV PDF (ou texte / exemple), extraction d’un profil structuré, éditable.
2. Normalisation des compétences vers un référentiel dérivé du corpus.
3. Recherche hybride : filtres déterministes, puis cosine.
4. Score à six dimensions, offres réparties en trois paniers.
5. Écarts dérivés du calcul, recommandations issues d’un catalogue fermé.
6. Simulation d’impact.

### 2.3 Périmètre volontaire

Sont exclus : CV scannés (pas d’OCR), documents multilingues, PDF trop graphiques, offres hors tech. La langue unique est l’anglais : les jeux publics d’offres riches le sont, les CV de test aussi.

Règle d’inclusion des champs : un attribut n’entre dans un schéma que s’il alimente un **filtre** ou une **dimension de score**. Tout le descriptif gratuit (hobby, photo, phrase d’accroche) est laissé de côté.

### 2.4 Corpus

120 offres filtrées depuis *Multi-ATS* (CC BY 4.0), 20 par famille (backend, frontend, data, devops, cybersecurity, technical_product), au plus 2 par entreprise. Le champ `job_description` source est un résumé LLM (~400 caractères) : on reconstitue un texte plus riche (résumé + responsabilités + qualifications). `skills_required` est rangé dans un sidecar **pour l’évaluation et la structuration d’offre**, pas injecté comme vérité dans l’extraction CV.

Le référentiel compte 154 compétences (minimum 3 occurrences). Union d’une extraction LLM sur les textes d’offres et des listes du dataset, fusion d’alias, denylist des soft skills. Les mentions 1–2 fois sont écartées comme bruit. Aucune compétence orpheline : le vocabulaire est ancré dans le corpus, pas dans ESCO.

---

## 3. Architecture

```
backend/src/career_match/
  domain/        schémas, normalisation, scoring — stdlib + Pydantic
  adapters/      LLM, embeddings, PDF, pgvector, MCP
  pipeline/      LangGraph (extract → normalize → retrieve → score)
  api/           FastAPI (façade, session, auth, chat)
  eval/          jeu annoté → score_offer
  cli/           indexation, match, MCP, serve, eval_cases
frontend/        Next.js (App Router), rewrite /api/* → :8000
```

### 3.1 Domain pur

`domain/` n’importe ni LangChain, ni Postgres, ni le réseau. Un test d’architecture parcourt les AST et échoue si la règle casse. Conséquence : le scoring et la cascade de normalisation se testent **sans mock** ; seuls l’extracteur et l’embedder sont des ports.

### 3.2 Deux couches de profil

`RawProfile` est la sortie LLM (pas de séniorité : elle serait inventée). `Profile` est la forme normalisée, seule consommée par le scoring. `user_edited` et `correction_count` mesurent la correction humaine comme proxy de qualité d’extraction, sans harness dédié.

Le schéma d’offre est le **miroir** du profil : mêmes familles, mêmes échelles ordinales, même référentiel. Sans ce vocabulaire partagé, le score n’est pas écrivable proprement.

### 3.3 Échelles

Les compétences sont sur 1–4 (AWARENESS, WORKING, PROFICIENT, EXPERT), avec définitions injectées dans le prompt. Une échelle 1–10 serait instable en sortie de modèle. La séniorité est un `IntEnum` (junior … lead) pour que l’écart candidat − offre soit signé.

### 3.4 Injection des dépendances

`PipelineDeps` porte extracteur, caches, embedder, index, offres structurées, catalogue, config, référentiel. L’état LangGraph (`MatchState`) ne contient pas ces objets : le graphe orchestre, il ne calcule pas.

---

## 4. Chaîne de matching

### 4.1 Extraction

PDF textuel (pypdf) → Groq GPT-OSS 20B, `response_format: json_object`, validation Pydantic. Le JSON Schema strict de Groq refuse les optionnels (`anyOf` sans discriminateur) : on n’utilise pas `with_structured_output(json_schema)`. Cache disque : hash du fichier + version de prompt + identifiant de modèle. La démo ne dépend plus d’un appel réseau après le premier passage.

Un mini-CV collé dans l’UI emprunte **le même extracteur** qu’un PDF.

### 4.2 Normalisation (déterministe)

Cascade : correspondance exacte, puis alias, puis fuzzy (seuil 0,88). Pas de LLM en dernier recours, pas d’embeddings à cette étape. Les mentions non résolues sont journalisées (bruit / inconnu / ambigu). Séniorité dérivée des années : &lt; 2 junior, &lt; 5 mid, &lt; 10 senior, sinon lead. Niveau manquant = WORKING.

### 4.3 Offres structurées

Pas de second LLM sur les 120 textes. Le sidecar `skills_required` passe par la même cascade. Les 5 compétences les plus fréquentes du référentiel deviennent *mandatory*, le reste *preferred*. Famille, lieu et *work_model* viennent des annotations, pas d’une extraction.

### 4.4 Recherche hybride (RAG)

1. **Filtres** : famille cible, *work_model* si renseigné, lieu si le candidat n’est pas mobile. Une offre sans *work_model* n’est pas éliminée (donnée manquante).
2. **Cosine** pgvector sur titre + description. Embeddings OpenAI `text-embedding-3-small` (1536). Groq ne fournit pas d’embeddings. Cache disque des vecteurs. Indexation unique (quelques centimes).

Le cosine **entre** dans le domain comme un `float` (dimension *semantic*). `domain` n’appelle pas pgvector. Ce n’est pas un chatbot sur les fiches de poste : c’est un retrieve-then-score.

### 4.5 Score, paniers, gaps, simulation

Six dimensions dans `[0, 1]`, pondérées (politique live, après semaine 7) :

| Dimension | Poids |
|---|---|
| mandatory_skills | 0,40 |
| preferred_skills | 0,15 |
| seniority | 0,15 |
| semantic | 0,15 |
| education | 0,10 |
| languages | 0,05 |

Le total est sur 100. **Le panier ne se déduit pas de ce total.** Il dépend des écarts mandatory et de la séniorité :

- écart séniorité ≤ −3 → `out_of_reach`
- 0 mandatory manquante et écart ≥ −1 → `eligible`
- jusqu’à 3 mandatory manquantes et écart ≥ −2 → `reachable`
- sinon `out_of_reach`

Un *preferred* manquant coûte des points, jamais le panier. Les *gaps* sont le journal des mêmes comparaisons, pas un second modèle.

Le catalogue de formations est **fermé**. Un cours clone le profil, ajoute ou relève une compétence, puis on re-score. Pas de génération libre de MOOC. C’est le geste d’oral le plus clair : avant / après, panier avant / après.

### 4.6 LangGraph

Graphe linéaire, un branchement : PDF → extract → normalize ; JSON `Profile` → retrieve (on saute extract/normalize) ; JSON `RawProfile` → normalize encore. Puis retrieve → score, toujours. `score_retrieved` reprend la boucle de `match_profile` : le nœud score ne re-cherche pas. La CLI semaine 3 (`match_profile`) reste ; `run_pipeline` produit le même JSON (`card_payload`) via le graphe, pour que les deux entrées restent comparables à l’oral.

---

## 5. Rôles de l’IA

L’IA n’est pas un agent unique. Trois familles d’acteurs, et le score n’est dans aucune.

### 5.1 Modèles

- **LLM de chat** (défaut Groq `openai/gpt-oss-20b` ; alternative OpenAI `gpt-4o-mini` via `LLM_PROVIDER`). Rôle : remplir un `RawProfile` depuis le texte du CV ; extraire des labels pour **construire** le référentiel (hors ligne). Il ne normalise pas, ne score pas, ne choisit pas le panier.
- **Embeddings** OpenAI `text-embedding-3-small`. Rôle : vecteurs pour le cosine. Ils ne filtrent pas, ils ne calculent pas le 0–100.

La fabrique (`build_profile_extractor`, `build_chat_llm`) masque Groq et OpenAI. Les CLI n’instancient plus un provider en dur. Anthropic n’est pas branché.

### 5.2 Agent conversationnel

`POST /api/chat` : LLM + outils sur la **session déjà scorée**. Outils : `list_matched_offers`, `get_matched_offer`, `get_session_profile`, `simulate_catalogue_course` (même `simulate_course` que le MCP). Le prompt système interdit de citer un chiffre absent du JSON outils. `tools_used` dans la réponse rend l’appel visible (Swagger, tests scriptés). Boucle bornée (6 pas). Pas de streaming, pas d’historique long.

### 5.3 MCP

Cinq outils stdio (FastMCP) : `extract_profile`, `normalize_profile`, `search_offers`, `match_profile`, `simulate_course`. Les corps appellent les nœuds / le graphe / le domain. Le serveur n’invente pas de score. Le client spawn un process séparé, **découvre** les outils (`list_tools`), puis appelle : MCP n’est pas un import déguisé.

### 5.4 Orchestrateurs (pas des modèles)

- **LangGraph** : enchaîne les nœuds. Pas de LLM dans normalize / retrieve / score.
- **n8n** : trigger → `POST /api/match` (exemple Jane Doe) → décompte des paniers. Il orchestre, il ne calcule pas.

Phrase de soutenance : *le LLM structure, l’embedder rapproche, l’agent explique, le domain décide.*

---

## 6. Application

### 6.1 API FastAPI

Façade sur `run_matching` + `card_payload`. OpenAPI est la source de vérité (`/docs`, `/redoc`) ; `docs/api.md` pointe vers ces URLs sans recopier les champs.

`POST /api/match` accepte **exactement une** source : JSON `text`, JSON `example` (`jane_doe_backend`), ou multipart `cv`. Cookie httponly `cm_session` (24 h, SameSite=Lax). Les cartes vivent en RAM ; le cookie n’est que l’identifiant. `GET /api/offers` et `GET /api/offers/{source_id}` relisent sans rescoring. CORS : localhost:3000 / 5173, credentials.

`PUT /api/profile` pose `user_edited` et incrémente `correction_count` **sans** relancer le graphe. `POST /api/rematch` écrit un JSON Profile temporaire (chemin graphe sans extract).

### 6.2 Auth « essayer puis sauver »

Le match n’est pas un paywall. Un compte (email + mot de passe, pbkdf2) persiste le Profile et les dernières cartes. Un compte = un profil. À l’inscription / login, la session en RAM **gagne** ; sinon on rehydrate depuis `data/cache/accounts.json` (gitignoré). Logout enlève le lien compte, **garde** les cartes. Pas d’OAuth.

### 6.3 Front Next.js

App Router, rewrite `/api/*` → `localhost:8000`. Accueil (formulaire toujours, pour pouvoir relancer un match), liste à trois paniers, fiche (six barres, gaps, simulations), `/profile`, overlay login, tiroir chat. Le front n’invente aucun score.

### 6.4 Tests

Stratégie : unitaires sur le déterministe (domain, paniers, cascade) ; fakes pipeline pour l’API (pas de Postgres, pas de LLM live) ; client MCP contre un serveur de test ; 12 cas annotés sur `score_offer`. Le chat HTTP est testé avec un client LLM **scripté** qui force un tool call, puis une réplique.

---

## 7. Évaluation

Les tests unitaires ne disent pas si la **politique de paniers** est juste face au sidecar (souvent cinq compétences mandatory). La semaine 7 introduit un jeu **or** : 12 paires profil × offre, un panier attendu, pas un score cible.

Trois profils figés : Jane (senior backend, Python / Kubernetes / AWS…), Maya (mid frontend, React / TypeScript / Next.js), Leo (junior data, Python / SQL). Le runner `eval_cases` charge le corpus structuré et appelle `score_offer`. Les filtres de retrieval sont hors scope : on juge les paniers, pas le rappel de l’index.

Résultat : **12/12** après la seconde passe.

Seconde passe (`data/processed/scoring.json` seulement) :

- `max_mandatory_gaps_reachable` : 2 → 3
- poids *semantic* : 0,20 → 0,15 ; *mandatory_skills* : 0,35 → 0,40

Exemple : Jane + « Senior Backend Engineer (Distributed Systems) » (aws et kubernetes ok, azure / java / go manquent) tombait en `out_of_reach` avec max = 2. Avec max = 3, elle est `reachable` : un chemin de cours, pas un mur. `DEFAULT_SCORING_CONFIG` (Python) reste la politique semaine 3, pour ne pas casser les tests unitaires historiques.

Limite assumée : 12 cas ne mesurent pas la qualité de l’extraction LLM. Ce serait une annotation v2 (profils extraits vs profils corrigés, taux de `correction_count`).

---

## 8. Démonstration

La démo orale (~8–10 min) suit [demo.md](demo.md). Contrainte opérationnelle : rester sur `http://localhost:3000` (ne pas mélanger avec `127.0.0.1`, le cookie disparaît).

Enchaînement montré :

1. Invité, chip Jane Doe → trois paniers (*on range, on ne jette pas*).
2. Fiche *reachable* / *out_of_reach* : score, six axes, gaps, simulation.
3. Profil : correction, Save sans rescoring, Recalculer.
4. Compte : le match n’était pas bloqué.
5. Chat : « Why is this offer… ? » / « Which course helps most ? » — chiffres issus des outils.

Filet : si Groq gère mal les tool calls, `LLM_PROVIDER=openai`. Si le chat hallucine, Swagger et `tools_used` démontrent encore le contrat.

---

## 9. Limites et perspectives

Le journal (`docs/journal.md`) alimente cette section. Synthèse :

| Limite | Pourquoi | V2 |
|---|---|---|
| Pas d’OCR, anglais seulement, tech seulement | 8 semaines, démontrer l’IA plutôt que la robustesse | OCR, langue, multi-domaines |
| Résumés LLM dans le dataset d’offres | Corpus public | Vraies annonces |
| Référentiel maison (154) | Ancré dans les données, pas orphelin | ESCO / O\*NET |
| Session et comptes en RAM / JSON | Suffisant pour la démo | Redis, reset password, OAuth |
| Chat sans streaming ni mémoire longue | Contrôle du coût et des tests | Historique, HTTP MCP |
| 12 cas, politique de paniers seulement | Mesurer le déterministe face au sidecar | Annoter l’extraction |
| Cap 5 mandatory sur l’offre | Heuristique de structuration | Recalibrer le cap |
| Jane remote-only vs corpus souvent onsite | Filtre *work_model* honnête, parfois vide | Assouplir ou annoter le travail à distance |

Ces raccourcis sont des choix, pas des oublis : chaque ligne du journal porte une raison et une piste v2.

---

## 10. Conclusion

career-match montre une chaîne complète de matching **explicable**. L’apport n’est pas un LLM qui « note » des CV : c’est la séparation nette entre ce qui est incertain (extraction, embeddings) et ce qui est justiciable (normalisation, filtres, six axes, trois paniers, simulation sur catalogue fermé).

Les notions du cursus s’incarnent sans se confondre : LangChain / Groq / OpenAI derrière une fabrique ; RAG = filtres puis cosine ; LangGraph orchestre sans recalculer ; MCP et le chat agent **réutilisent** le domain ; n8n consomme l’API.

Le jalon pivot (semaine 3, CLI `match_profile`) tenait déjà sans graphe ni front. Les semaines suivantes n’ont pas réécrit le score : elles l’ont exposé, évalué, et raconté.

---

## Références internes

- Décisions : [journal.md](journal.md)
- Démo : [demo.md](demo.md)
- API : [api.md](api.md) et `http://127.0.0.1:8000/docs`
- Éval : [eval.md](eval.md)
- n8n : [n8n.md](n8n.md)
- Maquettes : [wireframes/README.md](wireframes/README.md)
