"""Embedding via a local Ollama model (nomic-embed-text).

Isolated behind one class so the embedding model can be swapped without touching
the rest of the pipeline.
"""

from __future__ import annotations

import ollama

DEFAULT_MODEL = "nomic-embed-text"


class Embedder:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""
        vectors: list[list[float]] = []
        for text in texts:
            resp = ollama.embeddings(model=self.model, prompt=text)
            vectors.append(resp["embedding"])
        return vectors

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]
