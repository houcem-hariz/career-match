# Journal des décisions et des raccourcis

Une ligne par décision, au moment où elle est prise. Ce fichier alimente directement
la section « limites et perspectives » du rapport final.

Format : **date — décision** / raison / ce qui serait fait en v2.

---

## Semaine 1

**2026-08-19 — Périmètre volontairement restreint aux scénarios cadrés.**
Les cas dégradés (CV scannés nécessitant de l'OCR, CV multilingues, PDF à mise en page
graphique, offres hors du domaine tech) sont exclus. Raison : projet académique de 8 semaines
à 14h par semaine, l'objectif est de démontrer la maîtrise des notions d'IA, pas la robustesse
industrielle. En v2 : OCR, détection de langue, corpus multi-domaines.

**2026-08-19 — Langue unique du corpus et des CV : anglais.**
Raison : les datasets publics d'offres riches sont majoritairement anglophones. Conséquence
assumée : les CV de test doivent également être en anglais. En v2 : détection et gestion
multilingue.

**2026-08-19 — Identifiants et code en anglais, documentation et rapport en français.**
Raison : convention de développement d'un côté, livrable académique de l'autre.

**2026-08-19 — Le paquet domain ne dépend d'aucune librairie externe : ni LangChain, ni base
de données, ni réseau.**
Raison : c'est ce qui rend la logique de scoring et de normalisation testable unitairement
sans mock, et c'est le socle de la stratégie de test (tests unitaires sur le déterministe,
jeu de cas annoté sur le probabiliste). Un test d'architecture automatisé vérifie cette règle.

**2026-08-19 — Le profil est stocké en deux couches : brut et normalisé.**
Raison : isole la partie incertaine (la normalisation vers le référentiel) de la partie
déterministe (le scoring), et permet de mesurer le taux de correction humaine comme métrique
de qualité de l'extraction.

**2026-08-19 — Échelle de niveau de compétence ordinale 1 à 4, avec définitions explicites.**
Raison : une échelle 1-10 serait injustifiable et instable en sortie de LLM.
En v2 : calibrage sur un référentiel externe type ESCO.

**2026-08-19 — Le schéma d'offre est le miroir du schéma de profil.**
Raison : sans vocabulaire partagé (mêmes familles, mêmes échelles, même référentiel de
compétences), le scoring n'est pas écrivable proprement.

**2026-08-19 — Règle d'inclusion des champs : un champ n'entre dans un schéma que s'il est
consommé par le scoring ou par un filtre.**
Raison : chaque champ coûte de la complexité de prompt, du formulaire à coder et de la
logique de scoring.

**2026-08-19 — Cache disque des extractions dès le premier appel.**
Clé = hash du fichier source plus version du prompt. Raison : maîtrise du coût en
développement et sécurisation de la démo, qui ne dépend plus d'un appel réseau.

**2026-08-19 — Le référentiel de compétences est dérivé du corpus d'offres, pas construit
a priori.**
Raison : moins coûteux, plus défendable car ancré dans les données, et aucune compétence
orpheline. En v2 : alignement sur une taxonomie externe (ESCO, O*NET).

**2026-08-19 — Corpus : 120 offres filtrees depuis Multi-ATS parquet (CC BY 4.0).**
Le champ job_description du dataset est un resume LLM (~400 caracteres), pas l'annonce originale.
On reconstitue un texte plus riche en concatenant resume + responsabilites + qualifications.
skills_required est range dans un sidecar pour evaluation, pas injecte dans l'extraction.
20 offres par famille, max 2 par entreprise. En v2 : vraies annonces completes.

**2026-08-20 — Extraction CV : Groq GPT-OSS 20B, JSON object + validation Pydantic.**
Le JSON schema strict de Groq refuse les champs optionnels (anyOf sans discriminateur), donc on n'utilise pas with_structured_output(json_schema).
Cache disque : hash du PDF + version de prompt + modele. En v2 : sortie schema-native chez un provider qui la supporte vraiment.

**2026-08-21 — Referentiel derive du corpus : 154 competences, min 3 occurrences.**
Union extraction LLM (GPT-OSS 20B) + listes skills du dataset, puis fusion d'alias et denylist (soft skills).
Les mentions rares (1-2) sont ecartees comme bruit. En v2 : alignement ESCO.

