"""Postgres + pgvector store for offer embeddings."""

from __future__ import annotations

from dataclasses import dataclass

import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector

from career_match.domain.models.enums import JobFamily
from career_match.domain.retrieval.filters import RetrievalFilters
from career_match.domain.retrieval.results import RetrievedOffer


@dataclass(frozen=True)
class IndexedOffer:
    source_id: str
    title: str
    company: str | None
    description: str
    location_text: str | None
    family: JobFamily
    work_model: str | None
    embedding: list[float]
    embedding_model: str


class PostgresOfferIndex:
    def __init__(self, database_url: str, dimensions: int) -> None:
        if dimensions < 1:
            raise ValueError("embedding dimensions must be positive")
        self._database_url = database_url
        self._dimensions = int(dimensions)

    def ensure_schema(self) -> None:
        with psycopg.connect(self._database_url) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.commit()
        with self._connect() as conn:
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS offers (
                    source_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    company TEXT,
                    description TEXT NOT NULL,
                    location_text TEXT,
                    family TEXT NOT NULL,
                    work_model TEXT,
                    embedding vector({self._dimensions}) NOT NULL,
                    embedding_model TEXT NOT NULL,
                    indexed_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS offers_embedding_hnsw_idx
                ON offers USING hnsw (embedding vector_cosine_ops)
                """
            )
            conn.commit()

    def upsert(self, rows: list[IndexedOffer]) -> None:
        if not rows:
            return
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO offers (
                        source_id, title, company, description, location_text,
                        family, work_model, embedding, embedding_model
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        company = EXCLUDED.company,
                        description = EXCLUDED.description,
                        location_text = EXCLUDED.location_text,
                        family = EXCLUDED.family,
                        work_model = EXCLUDED.work_model,
                        embedding = EXCLUDED.embedding,
                        embedding_model = EXCLUDED.embedding_model,
                        indexed_at = now()
                    """,
                    [
                        (
                            row.source_id,
                            row.title,
                            row.company,
                            row.description,
                            row.location_text,
                            row.family.value,
                            row.work_model,
                            Vector(row.embedding),
                            row.embedding_model,
                        )
                        for row in rows
                    ],
                )
            conn.commit()

    def search(
        self,
        query: list[float],
        filters: RetrievalFilters,
        k: int,
    ) -> tuple[tuple[RetrievedOffer, ...], int]:
        where_sql, filter_params = _filter_sql(filters)
        vector = Vector(query)
        with self._connect() as conn:
            count_row = conn.execute(
                f"SELECT count(*) FROM offers {where_sql}",
                filter_params,
            ).fetchone()
            assert count_row is not None
            candidate_count = count_row[0]
            if not isinstance(candidate_count, int):
                raise TypeError(f"unexpected count type: {type(candidate_count)}")
            rows = conn.execute(
                f"""
                SELECT source_id, title, company, description, location_text,
                       family, work_model, 1 - (embedding <=> %s) AS similarity
                FROM offers
                {where_sql}
                ORDER BY embedding <=> %s
                LIMIT %s
                """,
                (vector, *filter_params, vector, max(k, 0)),
            ).fetchall()
        hits = tuple(_row_to_retrieved(row) for row in rows)
        return hits, candidate_count

    def count(self) -> int:
        with self._connect() as conn:
            result = conn.execute("SELECT count(*) FROM offers").fetchone()
            assert result is not None
            value = result[0]
            if not isinstance(value, int):
                raise TypeError(f"unexpected count type: {type(value)}")
            return value

    def counts_by_family(self) -> dict[str, int]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT family, count(*) FROM offers GROUP BY family ORDER BY family"
            ).fetchall()
        counts: dict[str, int] = {}
        for family, count in rows:
            if not isinstance(family, str) or not isinstance(count, int):
                raise TypeError("unexpected family count row")
            counts[family] = count
        return counts

    def _connect(self) -> psycopg.Connection[tuple[object, ...]]:
        conn = psycopg.connect(self._database_url)
        register_vector(conn)
        return conn


def _filter_sql(filters: RetrievalFilters) -> tuple[str, tuple[object, ...]]:
    clauses: list[str] = []
    params: list[object] = []
    if filters.families:
        clauses.append("family = ANY(%s)")
        params.append([family.value for family in filters.families])
    if filters.work_models:
        clauses.append("(work_model IS NULL OR work_model = ANY(%s))")
        params.append(list(filters.work_models))
    if filters.apply_location:
        patterns = [f"%{needle}%" for needle in filters.locations]
        clauses.append("(location_text IS NULL OR location_text ILIKE ANY(%s))")
        params.append(patterns)
    if not clauses:
        return "", ()
    return "WHERE " + " AND ".join(clauses), tuple(params)


def _row_to_retrieved(row: tuple[object, ...]) -> RetrievedOffer:
    source_id, title, company, description, location_text, family, work_model, similarity = row
    if not isinstance(source_id, str) or not isinstance(title, str) or not isinstance(family, str):
        raise TypeError("unexpected offer row types")
    if not isinstance(description, str):
        raise TypeError("unexpected description type")
    return RetrievedOffer(
        source_id=source_id,
        title=title,
        company=company if isinstance(company, str) else None,
        family=JobFamily(family),
        location_text=location_text if isinstance(location_text, str) else None,
        work_model=work_model if isinstance(work_model, str) else None,
        similarity=round(float(similarity), 4),  # type: ignore[arg-type]
        description=description,
    )
