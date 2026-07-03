"""Retrieval: question -> relevant context for the LLM.

Matches on section-level chunks, then (Phase 4) expands to parent notes so the
LLM gets complete context. Phase 2 can start with plain top-k chunks.
"""

from __future__ import annotations

from dataclasses import dataclass

from .embedder import Embedder
from .store import Store


@dataclass
class Retrieved:
    text: str
    title: str
    source_path: str
    score: float | None = None


def retrieve(
    question: str,
    store: Store,
    embedder: Embedder,
    k: int = 4,
    where: dict | None = None,
) -> list[Retrieved]:
    """Embed the question, return top-k matching chunks.

    Phase 2: return the matched chunks directly.
    Phase 4 (TODO): dedupe by parent_id and swap in the full parent note text
    (parent-document retrieval), and support `where` metadata filters.
    """
    qvec = embedder.embed_one(question)
    res = store.query(qvec, n_results=k, where=where)

    hits: list[Retrieved] = []
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[None] * len(docs)])[0]
    for doc, meta, dist in zip(docs, metas, dists):
        hits.append(
            Retrieved(
                text=doc,
                title=meta.get("title", "?"),
                source_path=meta.get("source_path", "?"),
                score=dist,
            )
        )
    return hits
