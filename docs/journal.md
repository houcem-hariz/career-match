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

## Semaine 2

**2026-08-25 — Normalisation deterministe : exact, puis alias, puis fuzzy (seuil 0.88).**
Pas de LLM en dernier recours, pas d'embeddings pour cette etape. Les mentions non resolues sont journalisees (bruit / inconnu / ambigu). Seniorite derivee des annees : <2 junior, <5 mid, <10 senior, sinon lead. Niveau manquant = WORKING. En v2 : etape embeddings dans la cascade.

**2026-08-25 — Embeddings : OpenAI text-embedding-3-small (1536 dimensions).**
Groq ne fournit pas d'embeddings. OpenAI small suffit pour 120 offres (quelques centimes, indexation unique). Alternative locale (BGE / Ollama) conservee comme v2 si le corpus grossit. Changer de modele impose de re-indexer pgvector.

**2026-08-25 — Index offres : Postgres + pgvector en local (Docker, port 5433).**
Texte embedde = titre + description. Cache disque des vecteurs (modele + version de texte). Famille et lieu viennent des annotations, pas d'une extraction LLM. En v2 : extraction structuree des offres pour le scoring.

**2026-08-25 — Recherche hybride : filtres deterministes puis cosine pgvector.**
Famille / lieu / mode de travail eliminent avant le ranking semantique. Lieu ignore si willing_to_relocate. Offre sans work_model non eliminee (donnee manquante). Le scoring 6 dimensions reste semaine 3.

**2026-08-29 — Couche agnostique : Groq et OpenAI derriere la meme fabrique.**
LLM_PROVIDER=groq | openai. Meme prompt, meme RawProfile. Defaut Groq (GPT-OSS 20B). OpenAI chat = gpt-4o-mini, embeddings inchanges. Les CLI n'instancient plus Groq en dur. Anthropic non branche.

## Semaine 3

**2026-08-30 — Offres structurees depuis les annotations + le referentiel, pas un second LLM.**
skills_required du sidecar passe par la meme cascade que le CV. Les 5 competences les plus frequentes du referentiel deviennent mandatory, le reste preferred. Les soft skills tombent comme a la construction du referentiel. Raison : 120 textes identiques a extraire une deuxieme fois n ajouteraient que du cout et du bruit. En v2 : extraction structuree des offres si le corpus n a plus de sidecar.

**2026-08-30 — Scoring a six dimensions, poids dans data/processed/scoring.json.**
mandatory 0.35, preferred 0.15, seniority 0.15, education 0.10, languages 0.05, semantic 0.20. La similarite cosine vient de la recherche et entre dans domain comme un float : domain n appelle pas pgvector. Lieu et work_model restent des filtres, pas des axes de score.

**2026-08-30 — Trois paniers determines par les ecarts mandatory et la seniorite.**
ecart seniorite = candidat - offre. <= -3 : out_of_reach. 0 mandatory manquante et ecart >= -1 : eligible. <= 2 mandatory et ecart >= -2 : reachable. Sinon out_of_reach. Un preferred manque coute des points, jamais le panier. Les gaps sont le journal des memes comparaisons.

**2026-08-30 — Catalogue ferme + simulation d impact, CLI match_profile.**
Un cours clone le profil, ajoute ou releve une competence, puis on re-score. Pas de generation libre de formations. La CLI enchaine extract/normalize (si PDF), recherche, score, paniers, gaps, simulation. Jalon pivot : la chaine complete tient sans LangGraph ni front. En v2 : catalogue plus large, multi-competences par cours.

## Semaine 4

**2026-09-01 — Pipeline : etat + noeuds avant le graphe LangGraph.**
MatchState est un TypedDict in-process (objets domain, pas encore du JSON). Quatre noeuds (extract, normalize, retrieve, score) appellent les fonctions semaine 3. Le score ne re-cherche pas : score_retrieved reprend la boucle de match_profile. Les dependances (extracteur, pgvector, referentiel) sont injectees via PipelineDeps, pas dans l etat. En v2 : serialisation de l etat pour un graphe distribue.

**2026-09-01 — Graphe LangGraph lineaire, un seul branchement PDF / JSON.**
PDF : extract puis normalize. JSON Profile (cle profile_id) : on saute extract et normalize. JSON RawProfile : on saute extract, on normalise encore. Ensuite retrieve puis score, toujours. Le graphe n orchestre pas le calcul du score. En v2 : retry / humain dans la boucle.

**2026-09-05 — CLI run_pipeline : meme JSON que match_profile, via le graphe.**
La CLI semaine 3 reste. run_pipeline construit PipelineDeps depuis settings + fichiers processed, puis invoke LangGraph. Le payload JSON est partage (card_payload) pour que les deux entrees restent comparables a l oral. En v2 : une seule CLI, match_profile delegue au graphe.
