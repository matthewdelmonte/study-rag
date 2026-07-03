# Personal Study RAG — System Architecture

**Author:** Matthew · **Date:** 2026-07-02
**Goal:** A fully-local retrieval-augmented knowledge base over personal AI-infrastructure study material (Obsidian markdown, PDFs, clipped articles). Doubles as an AI-infra portfolio project.

---

## 1. Design principles

1. **Normalize, then ingest.** Every source becomes clean markdown *before* it touches the vector store. One ingestion path, not three.
2. **One idea per chunk.** Follow logical structure; embed discrete sections, use parent-document retrieval for completeness.
3. **Local & private.** Personal notes never leave the machine. Embeddings + LLM run locally.
4. **Observable.** Every answer can name the notes it used. Retrieval is inspectable.
5. **Portfolio-grade.** Clean module boundaries, a CLI, and an eval set.

---

## 2. High-level flow

```
                    ┌─────────────── INGESTION (offline) ───────────────┐
  Obsidian .md ─┐   │                                                    │
  PDFs        ──┼──▶│  normalize → markdown  →  chunk  →  embed  →  store │
  Article URLs ─┘   │      (per-source)      (section) (Ollama)  (Chroma)│
                    └────────────────────────────────────────────────────┘
                                                                  │
                    ┌──────────────── QUERY (online) ─────────────┼──────┐
   your question ──▶│  embed  →  retrieve top-k (+parent expand)   │      │
                    │            → assemble context → local LLM → answer  │
                    └────────────────────────────────────────────┼───────┘
                                                          cites source notes
```

---

## 3. Components

| # | Component | Responsibility | Local tech |
|---|-----------|----------------|------------|
| 1 | Loaders | Source type → markdown + metadata | `pathlib`, `pymupdf` |
| 2 | Chunker | Section-level chunks + parent metadata | rule-based |
| 3 | Embedder | Text → vector | Ollama `nomic-embed-text` |
| 4 | Store | Persist + nearest-neighbor search | ChromaDB |
| 5 | Retriever | top-k + parent-document expansion | Chroma query |
| 6 | Generator | Prompt → cited answer | Ollama `qwen2.5:14b-instruct` |
| 7 | Evaluator | Golden Q→note hit-rate | YAML + script |
| 8 | CLI | ingest / query / eval | typer |

---

## 4. Chunking strategy by source

| Source | Rule | Metadata |
|--------|------|----------|
| Obsidian topic-wiki | Split on `##`/`###` sections; embed section, return parent note | title, tags, path, section |
| PDF paper/textbook | Structure-aware split + overlap | title, section, page |
| Clipped article | Normalize to markdown first, then as above | title, url, tags |

**Parent-document retrieval:** embed small section chunks for precise matching, return the whole
single-topic note to the LLM for complete context.

---

## 5. Build phases

1. Skeleton + ingest Obsidian markdown
2. Retrieval + cited answering
3. PDFs + articles
4. Parent-doc retrieval + metadata filtering
5. Evaluation harness

See `DECISIONS.md` for the rationale behind each locked-in choice.
