# Design Decisions

A running log of decisions so any future session (or contributor) has full context.

---

### 2026-07-02 — Foundational decisions

**Use case.** Personal RAG over AI-infrastructure study material. Primary goal: learning +
a portfolio piece that demonstrates running a full local AI stack.

**Fully local stack.** Personal notes never leave the machine. Embeddings and LLM both run
locally via Ollama. Chosen over API options for privacy and portfolio value.

**Sources → one normalized path.** Obsidian markdown (primary), PDFs, and clipped article
URLs. Everything is normalized to clean markdown *before* ingestion, so the pipeline only ever
ingests markdown — one path, not three.

**Chunking: section-level, not note-level.** Reasoned through the embedding-averaging problem:
embedding a whole multi-section note averages its meaning and matches narrow queries poorly.
So we embed **discrete sections** (one idea per vector) for precise matching.

**Parent-document retrieval.** We embed small (section) chunks for matching, but **return the
whole note** to the LLM for complete context. This is safe here because each Obsidian wiki is a
single-topic document — returning the parent adds no off-topic content. Resolves the
small-vs-large chunk tension.

**Embeddings:** `nomic-embed-text` via Ollama (keeps everything on one runtime rather than also
managing a Python sentence-transformers model).

**Answering LLM:** `qwen2.5:14b-instruct` (with `llama3.1:8b` as a lighter option). Room to move
to a 32B quant later.

**Vector store:** ChromaDB, persistent local client.

**Hardware target:** MacBook Pro, M4 Max, 48 GB RAM, 40-core GPU. Ollama + Docker installed;
user has local-LLM experience. Comfortable headroom for all of the above.

---

### 2026-07-02 — Storage: Postgres + pgvector (replaces ChromaDB)

**Decision.** Use a single Postgres database with the `pgvector` extension for both the
relational data (notes, chunks, metadata) and the embedding vectors. This replaces ChromaDB.

**Why.** A RAG store needs two jobs: relational filtering (by tag / source / date) and vector
similarity. pgvector does both in one SQL query
(`... WHERE tag = ANY(tags) ORDER BY embedding <=> :q LIMIT k`). Benefits: one database instead
of two, a production-standard pattern (portfolio value), a reusable template for future projects,
and it uses tools already installed (Postgres in PyCharm, Docker).

**How it runs.** `pgvector/pgvector` Docker image via a `docker-compose.yml` committed to the
repo — reproducible and part of the reusable template.

**Proposed schema.**
- `notes` — one row per note (system of record): note_id (PK), title, source_type, source_path, tags.
- `chunks` — one row per section: chunk_id (PK), note_id (FK → notes), section, chunk_text,
  embedding `vector(768)`. Vector index (HNSW or IVFFlat) on `embedding`.

**Fixed embedding dimension.** `vector(768)` matches `nomic-embed-text`. Switching embedding
models later requires a column migration — an accepted, known cost.

**Tradeoff accepted.** More setup than Chroma's zero-config (a DB, a connection, schema/migrations),
but managing that stack *is* the AI-infra skill being built.

**Follow-up work (tomorrow / Phase 1–2):** add `docker-compose.yml` + `schema.sql`; rewrite
`study_rag/store.py` from Chroma to `psycopg` + `pgvector`; swap deps in `pyproject.toml`
(drop `chromadb`, add `psycopg[binary]`, `pgvector`). `store.py` is the only module that changes —
the rest of the pipeline is storage-agnostic.

---

### 2026-07-03 — pgvector migration implemented + Phase 1 wired

**What shipped.** The Postgres + pgvector store (decided 2026-07-02) is now implemented, and the
Phase 1 ingest path runs end-to-end (`load → chunk → embed → store`).

- **Schema (`schema.sql`)** applied on container init: `notes` + `chunks(embedding vector(768))`,
  **HNSW index with `vector_cosine_ops`** (no training step; pairs with normalized
  `nomic-embed-text`). Query with the `<=>` cosine-distance operator.
- **Store API (`store.py`)** — psycopg 3 + `pgvector`: `upsert_note`, `add_chunks`,
  `query(embedding, k, tags)` (returns clean row dicts), `count`. Connection via DSN, default
  overridable with the `STUDY_RAG_DSN` env var.
- **Host port 5433, not 5432.** A native Postgres already owns `localhost:5432`, so the container
  publishes on **5433** to avoid clashing with it. Default DSN points at 5433.
- **`vector` cast in queries.** The `<=>` operator has no implicit cast from `double precision[]`
  (unlike inserting into a vector column), so the query embedding is cast with `%(q)s::vector`.

**Chunker decisions (built interactively).** Split on `##`/`###` headings; text before the first
heading is an "intro" chunk. Each section is embedded prefixed with context
(`"Title > Heading\n\n<body>"`; intro is prefixed with the title alone) so short sections keep
topical anchoring. Empty sections are skipped; chunk indices are contiguous.

---

### 2026-07-04 — Idempotent re-ingest + nomic task prefixes

Two correctness/quality fixes from an architecture review, ahead of Phase 2.

**Re-ingest replaces a note's chunks atomically.** `chunk_id` is positional
(`note_id::index`), and the old `add_chunks` only upserted — so re-ingesting an
edited note left orphaned rows (a shrunk note kept its extra `::N` chunks; a
reordered note overwrote the wrong ones). `add_chunks` now takes an explicit
`note_id` and does `DELETE FROM chunks WHERE note_id = … ` then re-inserts, all
in one transaction. The note is the unit of atomic replacement. The CLI now
`upsert_note`s every note (even one with zero embeddable sections) so an
emptied note still clears its stale chunks while keeping its system-of-record row.

**Asymmetric embedding prefixes for `nomic-embed-text`.** The model is trained
with `search_document:` on stored text and `search_query:` on the query;
embedding both raw left recall on the table. `Embedder` gained `embed_documents`
/ `embed_query` (prefixes are constructor params, default nomic's, set to `""`
to disable for other models). Ingest uses the document prefix; the retriever
uses the query prefix. *Consistency note:* any store populated before this must
be re-ingested so stored vectors carry the document prefix — the live store was
empty at change time, so nothing to migrate.

Verified end-to-end against a throwaway `study_rag_verify` DB: prefixes reach
Ollama, and re-ingesting a 4→2→0-section note leaves exactly 0 orphan chunks.

---

### 2026-07-04 — Phase 2 scope: carried-over review items

The architecture review surfaced four more items. #1 (stale chunks) and the
nomic prefixes shipped above; the rest are folded into **Phase 2**:

- **`note_id` collisions across subfolders.** `note_id = note::<filename-stem>`
  but the loader `rglob`s the whole vault, so two same-named files in different
  folders collide and one silently overwrites the other. Fix: derive the id from
  the path relative to the vault root, not just the stem.
- **Store the parent-note body.** The headline design returns the *whole note*
  to the LLM (Phase 4), but `notes` holds only metadata. Add a `notes.body`
  column now (cheap while the schema is young) rather than re-reading from
  `source_path` at query time.
- **Widen tag parsing.** `_TAGS_LINE` only matches inline `tags: [a, b]`; it
  silently drops Obsidian's YAML block form (`tags:\n  - a`) and inline `#tags`.
  Tags drive Phase 4 filtering, so parse both frontmatter forms.
- **Doc drift.** `architecture.md` §2–3 still shows ChromaDB; update it to
  Postgres + pgvector so the portfolio artifact matches the code.

---

*Append new decisions below with a date heading.*
