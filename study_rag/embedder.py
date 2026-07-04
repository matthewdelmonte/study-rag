"""Embedding via a local Ollama model (nomic-embed-text).

Isolated behind one class so the embedding model can be swapped without touching
the rest of the pipeline.
"""

from __future__ import annotations

import ollama

DEFAULT_MODEL = "nomic-embed-text"

# nomic-embed-text is trained for asymmetric retrieval: stored text is embedded
# with a "search_document:" prefix and the query with "search_query:". Applying
# the matching prefix on each side measurably improves retrieval. Pass empty
# strings for a model that does not use task prefixes.
DOC_PREFIX = "search_document: "
QUERY_PREFIX = "search_query: "


class Embedder:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        doc_prefix: str = DOC_PREFIX,
        query_prefix: str = QUERY_PREFIX,
    ):
        self.model = model
        self.doc_prefix = doc_prefix
        self.query_prefix = query_prefix

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text (no prefixing)."""
        vectors: list[list[float]] = []
        for text in texts:
            resp = ollama.embeddings(model=self.model, prompt=text)
            vectors.append(resp["embedding"])
        return vectors

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed texts for storage, with the document task prefix."""
        return self.embed([self.doc_prefix + t for t in texts])

    def embed_query(self, text: str) -> list[float]:
        """Embed a search query, with the query task prefix."""
        return self.embed([self.query_prefix + text])[0]
