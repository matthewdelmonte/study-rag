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
    tags: list[str] | None = None,
) -> list[Retrieved]:
    """Embed the question, return top-k matching chunks.

    Phase 2: return the matched chunks directly.
    Phase 4 (TODO): dedupe by note_id and swap in the full parent note text
    (parent-document retrieval).
    """
    qvec = embedder.embed_query(question)
    rows = store.query(qvec, k=k, tags=tags)

    return [
        Retrieved(
            text=row["text"],
            title=row.get("title", "?"),
            source_path=row.get("source_path", "?"),
            score=row.get("distance"),
        )
        for row in rows
    ]
