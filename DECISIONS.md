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

*Append new decisions below with a date heading.*
