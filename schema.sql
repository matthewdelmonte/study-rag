-- study-rag schema: one Postgres DB for relational data + embedding vectors.
-- Applied automatically on first container init (mounted into
-- /docker-entrypoint-initdb.d/). Idempotent, so it is safe to re-run by hand.

CREATE EXTENSION IF NOT EXISTS vector;

-- notes: one row per source document (system of record).
CREATE TABLE IF NOT EXISTS notes (
    note_id     text PRIMARY KEY,
    title       text NOT NULL,
    source_type text NOT NULL,          -- "note" | "pdf" | "article"
    source_path text NOT NULL,
    tags        text[] NOT NULL DEFAULT '{}'
);

-- chunks: one row per embeddable section. Matches on the section vector,
-- carries note_id for parent-document retrieval (Phase 4).
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id   text PRIMARY KEY,
    note_id    text NOT NULL REFERENCES notes(note_id) ON DELETE CASCADE,
    section    text,
    chunk_text text NOT NULL,
    embedding  vector(768)              -- matches nomic-embed-text
);

CREATE INDEX IF NOT EXISTS chunks_note_id_idx ON chunks (note_id);

-- HNSW + cosine: no training step, strong recall, pairs with normalized
-- nomic-embed-text vectors. Query with the `<=>` (cosine distance) operator.
CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw_idx
    ON chunks USING hnsw (embedding vector_cosine_ops);
