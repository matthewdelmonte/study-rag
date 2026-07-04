# self-hosted-rag

A fully-local retrieval-augmented knowledge base over personal AI-infrastructure study notes
(Obsidian markdown, PDFs, clipped articles). Runs entirely on-device via Ollama (embeddings + LLM)
and Postgres + pgvector, orchestrated with Docker.

Built as a learning project and AI-infrastructure portfolio piece.

> Part of the broader [`ai-engineering`](../ai-engineering) career-transition plan — this repo is
> the live RAG implementation that informs **Project B (RFI/RFP Knowledge Agent)** in
> `docs/q2-projects.md`.

## Status

Building in phases — see `docs/architecture.md` and `DECISIONS.md`.

- [x] Project scaffold
- [x] **Phase 1** — ingest Obsidian markdown (loader → chunker → embed → store)
- [ ] Phase 2 — retrieval + cited answering
- [ ] Phase 3 — PDFs + articles
- [ ] Phase 4 — parent-doc retrieval + metadata filtering
- [ ] Phase 5 — evaluation harness

## Prerequisites

- Python ≥ 3.10
- [Docker](https://www.docker.com) — runs the Postgres + pgvector database via `docker-compose`
- [Ollama](https://ollama.com) running locally, with:
  - `ollama pull nomic-embed-text`   (embeddings)
  - `ollama pull qwen2.5:14b-instruct`   (answering — or `llama3.1:8b`)

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .

docker compose up -d   # start Postgres + pgvector (schema auto-applied on first run)
```

The store connects to `postgresql://study:study@localhost:5433/study_rag` by default
(host port **5433** to avoid clashing with a local Postgres on 5432). Override with the
`STUDY_RAG_DSN` env var or the `--dsn` flag on any command.

## Usage (target)

```bash
study-rag ingest /path/to/obsidian/vault   # embed notes into the local store
study-rag query "how does a KV cache evict under memory pressure?"
study-rag eval                              # run the golden-question hit-rate
```

## Layout

```
study_rag/
  loaders.py     # source → raw text + metadata
  chunker.py     # section-level chunks + parent metadata
  embedder.py    # Ollama nomic-embed-text wrapper
  store.py       # Postgres + pgvector store wrapper
  retriever.py   # top-k + parent-document expansion
  generator.py   # Ollama chat → cited answer
  cli.py         # ingest / query / eval
eval/golden.yaml # question → expected note
docs/            # architecture + decisions
schema.sql       # notes + chunks tables, HNSW cosine index (applied on DB init)
docker-compose.yml # Postgres + pgvector container (DB data lives in a Docker volume)
```
