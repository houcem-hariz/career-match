# Maquettes d'interface

Fil de fer de l'app (pas le design final). Home façon SuperCareer, suite
façon Jobbie : tout part d'un **profil**, pas d'une barre de recherche d'offres.

Invité d'abord, compte seulement pour **garder** le profil.

Ouvrir [index.html](index.html) en local pour tout voir d'un coup. Sur GitHub,
les SVG s'affichent directement ci-dessous.

## Navigation

```mermaid
flowchart TD
  start["/ Accueil"] -->|match| list["/offers Liste"]
  list -->|clic carte| detail["/offers/:id Detail"]
  detail -->|Offres| list
  list -->|Profil| profile["/profile"]
  profile -->|Recalculer| list
  profile -->|Nouveau profil| start
  list -.-> login["Login overlay"]
  list -.-> chat["Chat tiroir"]
```

Trait plein = démo. Pointillé = semaine 6, optionnel.

## Semaine 5

### 1. Accueil `/`

Logo + Se connecter. Zone texte (mini-CV) + PDF + 3 exemples.
Pas de bandeau Offres / Profil / Chat.

![Accueil](01-accueil.svg)

### 2. Liste `/offers`

Trois paniers. Nouveau profil sur cette page. Clic carte → détail.

![Liste](02-liste.svg)

### 3. Détail `/offers/:id`

Six dimensions, gaps, simulation. Retour ← Offres.

![Detail](03-detail.svg)

## Semaine 6

Bandeau : Offres · Profil · Chat. Login jamais bloquant.

### 4. Profil `/profile`

Corriger le Profile, Recalculer → liste.

![Profil](04-profil.svg)

### 5. Login (overlay)

Rattache le profil déjà en mémoire. Pas de re-dépôt du CV.

![Login](05-login.svg)

### 6. Chat (tiroir)

La page courante reste visible à gauche.

![Chat](06-chat.svg)
