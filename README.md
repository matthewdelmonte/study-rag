# study-rag

A fully-local retrieval-augmented knowledge base over personal AI-infrastructure study notes
(Obsidian markdown, PDFs, clipped articles). Runs entirely on-device via Ollama + ChromaDB.

Built as a learning project and AI-infrastructure portfolio piece.

## Status

Building in phases — see `docs/architecture.md` and `DECISIONS.md`.

- [x] Project scaffold
- [ ] **Phase 1** — ingest Obsidian markdown (loader → chunker → embed → store)
- [ ] Phase 2 — retrieval + cited answering
- [ ] Phase 3 — PDFs + articles
- [ ] Phase 4 — parent-doc retrieval + metadata filtering
- [ ] Phase 5 — evaluation harness

## Prerequisites

- Python ≥ 3.10
- [Ollama](https://ollama.com) running locally, with:
  - `ollama pull nomic-embed-text`   (embeddings)
  - `ollama pull qwen2.5:14b-instruct`   (answering — or `llama3.1:8b`)

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

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
  store.py       # ChromaDB persistent wrapper
  retriever.py   # top-k + parent-document expansion
  generator.py   # Ollama chat → cited answer
  cli.py         # ingest / query / eval
eval/golden.yaml # question → expected note
docs/            # architecture + decisions
data/            # local Chroma persistence (gitignored)
```
