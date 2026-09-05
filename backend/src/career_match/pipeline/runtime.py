"""Build live PipelineDeps from settings and on-disk artefacts."""

from __future__ import annotations

from pathlib import Path

from career_match.adapters.indexing.corpus import load_annotations
from career_match.adapters.ingestion.build_referential import load_offers
from career_match.adapters.ingestion.structure_offer import structure_corpus
from career_match.adapters.llm.factory import build_embedder, build_profile_extractor
from career_match.adapters.matching.config_io import load_scoring_config, load_training_catalogue
from career_match.adapters.storage.embedding_cache import EmbeddingCache
from career_match.adapters.storage.extraction_cache import ExtractionCache
from career_match.adapters.storage.offer_index import PostgresOfferIndex
from career_match.adapters.storage.referential_io import load_referential_index
from career_match.pipeline.deps import PipelineDeps
from career_match.settings import Settings, project_root


def default_data_paths() -> dict[str, Path]:
    root = project_root()
    return {
        "referential": root / "data" / "processed" / "referentiel.json",
        "scoring": root / "data" / "processed" / "scoring.json",
        "catalogue": root / "data" / "processed" / "training_catalog.json",
        "offers": root / "data" / "raw" / "offers" / "offers.jsonl",
        "annotations": root / "data" / "raw" / "offers" / "source_annotations.json",
    }


def build_live_deps(
    settings: Settings,
    *,
    referential_path: Path,
    scoring_path: Path,
    catalogue_path: Path,
    offers_path: Path | None = None,
    annotations_path: Path | None = None,
) -> PipelineDeps:
    paths = default_data_paths()
    index = load_referential_index(referential_path)
    store = PostgresOfferIndex(settings.database_url, settings.embedding_dimensions)
    store.ensure_schema()
    return PipelineDeps(
        extractor=build_profile_extractor(settings),
        extraction_cache=ExtractionCache(
            settings.extraction_cache_dir,
            settings.extraction_cache_enabled,
        ),
        embedder=build_embedder(settings),
        embedding_cache=EmbeddingCache(
            settings.embedding_cache_dir,
            settings.extraction_cache_enabled,
        ),
        store=store,
        offers_by_id=structure_corpus(
            load_offers(offers_path or paths["offers"]),
            load_annotations(annotations_path or paths["annotations"]),
            index,
        ),
        catalogue=load_training_catalogue(catalogue_path),
        config=load_scoring_config(scoring_path),
        referential=index,
    )
