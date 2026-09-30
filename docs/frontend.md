# Brief front (semaine 5) — Next.js

Document pour la personne qui code l’UI. Le backend **existe déjà**.
Le front n’invente aucun score : il affiche le JSON de l’API.

Maquettes : [wireframes/README.md](wireframes/README.md).
Contrat API : [api.md](api.md) et http://localhost:8000/docs (Swagger).

## Produit en une phrase

L’utilisateur pose **qui il est** (mini-CV, PDF, ou un exemple). L’app
renvoie des offres dans **3 paniers**, puis une fiche avec 6 axes, les
écarts, et « si je fais ce cours, le score / le panier change ».

Ce n’est **pas** une barre de recherche d’offres (pas « Dev React Paris »
comme mot-clé). Le texte = un petit CV.

## Prérequis

1. Docker Postgres + API allumés, depuis `backend/` :

   ```bash
   uv run python -m career_match.cli.serve
   ```

   API : `http://localhost:8000` (utiliser **localhost**, pas un mélange
   avec `127.0.0.1` — voir cookies plus bas).

2. Next.js (App Router) sur **`http://localhost:3000`**. Ce origin est
   déjà dans le CORS FastAPI, avec `credentials`.

3. Variable d’env, par exemple `NEXT_PUBLIC_API_URL=http://localhost:8000`.

## Cookies (critique)

`POST /api/match` pose un cookie httponly `cm_session`. Les GET suivants
en ont besoin.

- Tous les `fetch` vers l’API : `credentials: "include"`.
- Ne **pas** mélanger `localhost` et `127.0.0.1` (sites différents pour
  le navigateur → cookie invisible → `GET /api/offers` en 404).
- Option plus simple : **rewrite Next.js** `/api/:path*` →
  `http://localhost:8000/api/:path*` et n’appeler que des URLs relatives
  `/api/match`. Le navigateur ne parle qu’au port 3000.

Sans rewrite : `fetch("http://localhost:8000/api/match", { credentials: "include", ... })`.

## Routes Next.js (semaine 5 seulement)

| Page Next | Rôle | API |
|---|---|---|
| `app/page.tsx` → `/` | Obtenir un profil | `POST /api/match` |
| `app/offers/page.tsx` → `/offers` | 3 paniers | `GET /api/offers` |
| `app/offers/[sourceId]/page.tsx` | Détail d’une offre | `GET /api/offers/{source_id}` |

Pas de `/profile`, pas de chat, pas de login réel. Sur `/`, pas de liens
Offres / Profil / Chat. Dès qu’il y a un match, bandeau : logo + **Offres**.

Si `GET /api/offers` → 404 : rediriger vers `/`.

## 1. Accueil `/`

### UI

- Titre du type : *Trouvez les offres qui collent à votre profil.*
- Textarea (placeholder : `Senior backend, Python, 6 ans, remote...`)
- Input fichier PDF
- Bouton **Lancer le match** (actif s’il y a du texte **ou** un fichier)
- 3 chips cliquables

Exactement **une** source par requête (l’API refuse 400 si 0 ou 2).

### Chip 1 — démo Jane Doe (à faire en premier)

```http
POST /api/match?k=10
Content-Type: application/json

{"example": "jane_doe_backend"}
```

Seul `example` implémenté côté API aujourd’hui : `jane_doe_backend`.

### Chip 2 et 3 — texte prérempli (pas un second PDF)

Les chips *Frontend React, hybride, Paris* et *Data junior, Python*
n’ont **pas** encore de profil fichier. Pour la semaine 5 :

```http
POST /api/match
Content-Type: application/json

{"text": "Junior data analyst, Python, SQL, remote", "k": 10}
```

Le champ `text` est un **mini-CV en anglais** (corpus et extraction en
anglais), pas une query « jobs in Paris ».

### PDF

```http
POST /api/match?k=10
Content-Type: multipart/form-data

cv: <fichier.pdf>
```

En JS : `FormData`, champ nommé **`cv`** (pas `file`).

### Texte libre (textarea)

```http
POST /api/match
Content-Type: application/json

{"text": "Senior backend engineer, Python and Kubernetes, 6 years, remote", "k": 10}
```

Ne pas envoyer `text` + `example` ensemble → 400
`"Send exactly one of: a PDF (cv), text, or example (jane_doe_backend)."`

### Après le POST

- **200** : `router.push("/offers")`. Ne pas stocker les cartes dans
  `localStorage` : la session cookie suffit.
- **400** : afficher `response.json().detail` (string).
- Spinner pendant l’attente (extract LLM peut prendre plusieurs secondes
  hors cache).

### Exemple de 200 (forme)

Les vrais `source_id` / scores dépendent du corpus et du profil. La
**forme** est fixe :

```json
{
  "candidate_count": 7,
  "query_from_cache": true,
  "cards": [
    {
      "rank": 1,
      "bucket": "out_of_reach",
      "score": 54.2,
      "similarity": 0.81,
      "source_id": "offer_42",
      "title": "Staff Backend Engineer",
      "company": "Globex",
      "family": "backend",
      "seniority": "LEAD",
      "work_model": "remote",
      "dimensions": {
        "mandatory_skills": 0.4,
        "preferred_skills": 0.2,
        "seniority": 0.5,
        "education": 1.0,
        "languages": 1.0,
        "semantic": 0.81
      },
      "mandatory_gap_count": 3,
      "gaps": [
        {
          "kind": "skill",
          "skill_id": "react",
          "requirement": "mandatory",
          "have": null,
          "need": "WORKING",
          "detail": "mandatory react: have missing, need WORKING"
        }
      ],
      "simulations": [
        {
          "course_id": "intro-react",
          "title": "Intro to React",
          "skill_id": "react",
          "score_before": 54.2,
          "score_after": 61.0,
          "delta": 6.8,
          "bucket_before": "out_of_reach",
          "bucket_after": "reachable"
        }
      ]
    }
  ]
}
```

Types utiles :

- `bucket`: `"eligible"` | `"reachable"` | `"out_of_reach"`
- `dimensions.*`: nombre **0–1** (pas des %)
- `score`: **0–100**
- `seniority`: `"JUNIOR"` | `"MID"` | `"SENIOR"` | `"LEAD"` (nom enum)
- `work_model`: `"remote"` | `"hybrid"` | `"onsite"`
- `family`: `"backend"` | `"frontend"` | `"data"` | `"devops"` | `"cybersecurity"` | `"technical_product"`

Jane Doe **remote-only** : souvent **0 eligible**, beaucoup d’`out_of_reach`.
C’est normal, pas un bug UI. Une simulation peut passer une carte en
`reachable` : c’est l’écran détail pour l’oral.

## 2. Liste `/offers`

```http
GET /api/offers
Cookie: cm_session=...
```

Même JSON que le POST (`candidate_count` + `cards`).

- 404 → redirect `/` (pas de session / serveur redémarré).
- Grouper **côté front** : `eligible`, puis `reachable`, puis `out_of_reach`.
  L’API ne renvoie pas trois listes, un seul tableau déjà trié
  (panier puis score desc).
- Carte : `title`, `company`, `score` (arrondi 1 décimale ok), `bucket`.
- Clic → `/offers/${card.source_id}` (le `source_id`, pas `rank`).
- Ligne du type : `Jane · backend · remote · N offres` si tu as ces
  infos ; sinon `N offres` + `candidate_count` suffit en semaine 5
  (le GET ne renvoie pas encore le Profile).
- **Nouveau profil** : `router.push("/")`. Le prochain POST **écrase**
  la session. Pas d’endpoint DELETE pour l’instant.

Paniers vides : afficher le titre du groupe + une ligne *Aucune offre*
(Jane remote n’a souvent rien en Eligible).

## 3. Détail `/offers/[sourceId]`

```http
GET /api/offers/offer_42
```

200 = **un objet carte** (pas `{ "cards": [...] }`).

404 → retour liste, message *Offre inconnue dans cette session*.

Afficher :

1. Lien **← Offres** vers `/offers`
2. `title` · `company` · `bucket` · `score`
3. Les 6 `dimensions` (barres 0–1), labels :
   `mandatory_skills`, `preferred_skills`, `seniority`, `education`,
   `languages`, `semantic`
4. `gaps[]` : `detail` suffit ; `kind` / `skill_id` / `have` / `need` en plus
5. `simulations[]` : `{title} · {score_before} → {score_after} · {bucket_before} → {bucket_after}`

Ne pas appeler `POST /api/match` sur cette page.

## Exemple fetch (Next.js client)

```ts
const API = process.env.NEXT_PUBLIC_API_URL; // http://localhost:8000

export async function matchExample() {
  const res = await fetch(`${API}/api/match?k=10`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ example: "jane_doe_backend" }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail ?? res.statusText);
  }
  return res.json(); // MatchResponse
}

export async function listOffers() {
  const res = await fetch(`${API}/api/offers`, { credentials: "include" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("list failed");
  return res.json();
}

export async function getOffer(sourceId: string) {
  const res = await fetch(`${API}/api/offers/${sourceId}`, {
    credentials: "include",
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("detail failed");
  return res.json(); // CardPayload
}
```

Ces appels doivent tourner dans un **Client Component** (ou Route Handler
qui forward le `Cookie`). Un Server Component Next sans forward de cookie
ne verra pas `cm_session`.

## Hors scope (semaine 6)

Login / register, page `/profile`, tiroir chat, MCP, n8n.

Bouton **Se connecter** sur l’accueil : visuel ok, **sans** formulaire
qui marche.

## Design

Template / design system (shadcn, Mantine, etc.). Ne pas inventer une
charte. L’écran à soigner : **le détail** (l’oral).

## Checklist de recette

1. Chip Jane Doe → liste avec 3 sections (même vides).
2. F5 sur `/offers` : les cartes sont encore là (cookie).
3. Clic carte → 6 barres + gaps + au moins une simulation si le backend en envoie.
4. PDF réel (`data/raw/cvs/jane_doe_backend.pdf`) via upload.
5. Redémarrer l’API → `/offers` redirige vers `/`.
6. `localhost` partout, jamais mélangé avec `127.0.0.1`.
